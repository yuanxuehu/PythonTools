# PythonTools
Python脚本工具

## 一、检测iOS项目中未使用的方法脚本
FindSelectorsUnrefs.py
#使用示例：

```
python3 FindSelectorsUnrefs.py -a /Users/XXX/Library/Developer/Xcode/DerivedData/XXX-fqnqqxsirmzjmpgprzgvcvykqgot/Build/Products/Debug-iphonesimulator/XXX.app -p /Users/XXX/Projects/XXX -w XXX
```

#运行成功后会在当前目录下生成 find_selector_unrefs.txt文件 里面是工程中未使用到的方法

#先cd到脚本路径

### 1. python3 表示使用的python版本

### 2. FindSelectorsUnrefs.py 表示要执行的文件

### 3. -a XXX 代表需要分析的工程文件中生成的.app路径 在Products的XXX.app里 Show In Finder可以查看

### 4. -p 表示工程文件所在的路径

#其他扩展参数说明：-w 结果白名单处理，检测结果，只想要以什么开头的类的方法，多个用逗号隔开，比如JD,BD,AL

#-b 结果黑名单处理,检测结果，不想要以什么开头的类的方法，多个用逗号隔开,比如Pod,AF,SD

#-w 和 -b 不能共存，共存会报错




## 二、检测iOS项目无用类脚本
FindClassUnRefs.py，依赖于FindAllClassIvars.py
#使用示例：

```
python3 FindClassUnRefs.py -p /Users/XXX/Library/Developer/Xcode/DerivedData/XXX-fqnqqxsirmzjmpgprzgvcvykqgot/Build/Products/Debug-iphonesimulator/XXX.app -w XXX
```

#运行成功后会在当前目录下生成 find_class_unrefs.txt文件 里面是工程中未使用到的方法

参数使用同上

