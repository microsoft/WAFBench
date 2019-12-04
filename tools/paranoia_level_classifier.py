# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved. 
# Licensed under the MIT License.

import os
import re
import sys
import argparse
PARANOIA_LEVELS = [0, 1, 2, 3, 4]

def find_paranoia_level_line(lines = [], paranoia_level = 0):
    # find start
    start_pos = 0
    if paranoia_level > 0:
        start_pattern = re.compile(r"^\s*SecRule.*PARANOIA_LEVEL\D+" + str(paranoia_level) + r".*$")
        while start_pos < len(lines):
            if start_pattern.match(lines[start_pos]):
                break
            start_pos += 1

    # find end
    end_pattern = re.compile(r"^\s*SecRule.*PARANOIA_LEVEL\D+(\d+).*$")
    end_pos = start_pos + 1
    while end_pos < len(lines):
        result = end_pattern.match(lines[end_pos])
        if result and int(result.group(1)) > paranoia_level:
            break
        end_pos += 1
    if end_pos > start_pos and start_pos < len(lines):
        if end_pos > len(lines):
            end_pos = len(lines)
        return lines[start_pos + 1: end_pos]
    return []

def count_rules(lines):
    rules = []
    rule_pattern = re.compile(r"\s*[^#].*\Wid:(\d+).*")
    for line in lines:
        result = rule_pattern.match(line)
        if result:
            rules.append(result.group(1))
    return rules

def remove_paranoia_level_secrule(lines):
    i = 0
    rule_pattern = re.compile(r"^\s*SecRule.*PARANOIA_LEVEL\D+(\d+).*$")
    while i < len(lines):
        if rule_pattern.match(lines[i]):
            lines = lines[:i] + lines[i+1:]
        i += 1
    return lines

def count_paranoia_level(paths):
    targets = []
    for root, _, files in os.walk(paths):
        for file in files:
            if os.path.splitext(file)[-1] == ".conf":
                targets.append(os.path.join(root, file))

    paranoia_levels_counts = {}
    for path in targets:
        with open(path, "r") as fd:
            lines_buffer = fd.readlines()
            for level in PARANOIA_LEVELS:
                lines = find_paranoia_level_line(lines_buffer, level)
                lines = remove_paranoia_level_secrule(lines)
                paranoia_levels_counts.setdefault(level, []).extend(count_rules(lines))
    return paranoia_levels_counts

def classify_rules(args_rules, paranoia_map):
    rules = []
    for rule in args_rules:
        rule.strip('\n')
        rules.extend(rule.split())
    
    classify_result = {}
    for rule in rules:
        level = ''.join([str(k) for k,v in paranoia_map.items() if rule in v])
        if level != '':
            classify_result.setdefault(level, []).append(rule)
        else:
            classify_result.setdefault('Unknown', []).append(rule)
    return classify_result

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=
        '''
        Classify tesecases according to CRS paranoia level.
        You can use '--rules' to input rules which need to be classified.
        If you are not using '--rules' args, you can input rules in stdin and end with 'ctrl+d'.
        Output format: 
            paranoia_level rule_id_1 rule_id_2 ... rule_id_n
        E.G. 
        [input] python paranoia_level_classifier.py --crs owasp-modsecurity-crs/rules
        [input] python paranoia_level_classifier.py --crs owasp-modsecurity-crs/rules --rules 920120 933110 932100
        [out] 
            1 941120 933110
            3 920272
            4 920273
            Unknown 101010
        ''')

    parser.add_argument("-c", "--crs", help="path to CRS rules files(.conf)", required=True)
    parser.add_argument("-r", "--rules", help="rules needs to be classify", nargs='+', default=sys.stdin)
    args = parser.parse_args()

    reference_dict = count_paranoia_level(args.crs)
    classified_dict = classify_rules(args.rules, reference_dict)

    for paranoia_level, rules in classified_dict.items():
        print(paranoia_level, ' '.join(rules))

