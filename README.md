# PythonTools
Python3脚本工具

## 一、检测iOS项目中未使用的方法脚本
FindSelectorsUnrefs.py
## 使用示例：

```
python3 FindSelectorsUnrefs.py -a /Users/XXX/Library/Developer/Xcode/DerivedData/XXX-fqnqqxsirmzjmpgprzgvcvykqgot/Build/Products/Debug-iphonesimulator/XXX.app -p /Users/XXX/Projects/XXX -w XXX
```

## 运行成功后会在当前目录下生成 find_selector_unrefs.txt文件 里面是工程中未使用到的方法

## 先cd到脚本路径

### 1. python3 表示使用的python版本

### 2. FindSelectorsUnrefs.py 表示要执行的文件

### 3. -a XXX 代表需要分析的工程文件中生成的.app路径 在Products的XXX.app里 Show In Finder可以查看

### 4. -p 表示工程文件所在的路径

## 其他扩展参数说明：-w 结果白名单处理，检测结果，只想要以什么开头的类的方法，多个用逗号隔开，比如JD,BD,AL

## -b 结果黑名单处理,检测结果，不想要以什么开头的类的方法，多个用逗号隔开,比如Pod,AF,SD

## -w 和 -b 不能共存，共存会报错




## 二、检测iOS项目无用类脚本
FindClassUnRefs.py，依赖于FindAllClassIvars.py
## 使用示例：

```
python3 FindClassUnRefs.py -p /Users/XXX/Library/Developer/Xcode/DerivedData/XXX-fqnqqxsirmzjmpgprzgvcvykqgot/Build/Products/Debug-iphonesimulator/XXX.app -w XXX
```

## 运行成功后会在当前目录下生成 find_class_unrefs.txt文件 里面是工程中未使用到的方法

参数使用同上

## 原理：
## 利用Mach-O文件的结构：
##  - Mach-O文件的`__DATA __objc_classrefs`段记录了引用类的地址。
##  - `__DATA __objc_classlist`段记录了所有类的地址。
##  - 取差集就可以得到未使用的类的地址，然后进行符号化。

## 三、批量压缩图片脚本
使用前需替换Tinify API key 和输入输出路径，使用 pip 安装 Python 图像处理库 PIL（实际安装的是其维护分支 Pillow）pip install Pillow

## 使用示例：

```
python3 TinifyImageCompress.py
```

## 四、iOS OC工程未使用类检测脚本
完整分析（需Xcode生成Linkmap和Mach-O）：先用otool分析Mach-O获取类列表和引用列表；然后过滤特殊情况（父类、load方法类、动态调用类）；最后输出未使用类清单。对于无法获取Mach-O的情况，可以降级到代码扫描方案

## 使用示例：

```
 python3 /Users/TigerHu/Downloads/PythonTools/CheckOCProjectUnusedClass.py --project_path /Users/TigerHu/XcodeProjects/YourCompanyName/YourProjectName/ --macho_path /Users/TigerHu/Library/Developer/Xcode/DerivedData/xxx-fofkvptgsedrxmcavcsqvgzpbjyi/Build/Products/Debug-iphoneos/YourApp.app/YourApp --linkmap_path /Users/TigerHu/Library/Developer/Xcode/DerivedData/xxx-fofkvptgsedrxmcavcsqvgzpbjyi/Build/Intermediates.noindex/xxx.build/Debug-iphoneos/YourApp.build/YourApp-LinkMap-normal-arm64.txt
```


