#!/usr/bin/python3
class FrequencyToCode():
  def __init__(self, data):
    self.data = data

  def getCode(self):
    template = "#ifndef DATA_H\n#define DATA_H\nint FREQUENCIES[]=^{}$;\n"
    template += "int DURATION[]=^{}$;\n#endif"

    frequencies = str([i[0] for i in self.data])[1:-1]
    duration = str([i[1] for i in self.data])[1:-1]

    code = template.format(frequencies, duration)
    code = code.replace('^', '{').replace('$','}')
    return code

  def writeCode(self):
    f = open('data.h', 'w+')
    f.write(self.getCode())
    f.close()

d = [(1,1),(2,2),(3,3)]
X = FrequencyToCode(d)
X.writeCode()


