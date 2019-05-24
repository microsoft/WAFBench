import re

from ftw_compatible_tool import collector


class SwitchCollectWrapper(collector.SwitchCollector):
    def __init__(self, check_func, start_pattern, end_pattern, save_entire_line=False):
        self._check_func = check_func
        super(SwitchCollectWrapper, self).__init__(start_pattern, end_pattern, save_entire_line=save_entire_line)
    
    def _execute(self, collected_buffer, start_result, end_result):
        self._check_func(collected_buffer, start_result, end_result)


class Comparer(object):
        def __init__(self, expected):
            self.expected = expected
            self.hit_time = 0
        def __call__(self, collected_buffer, start_result, end_result):
            print("<"+collected_buffer+">")
            assert(re.match(self.expected, collected_buffer) is not None)
            self.hit_time += 1


def test_normal():

    c = Comparer("123")
    SwitchCollectWrapper(c, r"\D+", r"\D+")("abc123abc")
    assert(c.hit_time == 1)
    
    c = Comparer("^\d+$")
    SwitchCollectWrapper(c, r"\D+", r"(\D+|\Z)")("a1b1c1d1")
    assert(c.hit_time == 4)
    
    c = Comparer("")
    SwitchCollectWrapper(c, r"\d", r"\d")("abc123abc")
    assert(c.hit_time == 2)

    c = Comparer("")
    SwitchCollectWrapper(c, r"\d", r"\d")("abcd")
    assert(c.hit_time == 0)
    

def test_multiline():
    # multiline
    text = '''
            123-456
            789--0
            hello---world
    '''
    c = Comparer(r"^-{0,2}$")
    s = SwitchCollectWrapper(c, r"\d+", r"\d+")
    for line in text.splitlines():
        line = line.strip()
        s(line)
    assert(c.hit_time == 3)

    c = Comparer(r"^(\d+-{1,2}\d+)+$")
    s = SwitchCollectWrapper(c, r"\d+", r"\d+", save_entire_line = True)
    for line in text.splitlines():
        line = line.strip()
        s(line)
    assert(c.hit_time == 1)
