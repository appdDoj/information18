class Person(object):

    def __init__(self):
        self.name = "hh"

    def __eq__(self, other):
        return "哈哈"


if __name__ == '__main__':
    p1 = Person()
    p2 = Person()
    print(p1 == p2)