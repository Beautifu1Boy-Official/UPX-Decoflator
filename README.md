# UPX-Decoflator

一键 UPX 压缩并剥离特征的工具。把PE文件用upx加壳，然后去除upx壳的特征码，降低文件被静态查杀的概率。

如果文件已经加过 UPX 壳，会自动跳过压缩，直接做特征剥离。

## 概述

1. `upx --best --force` 最大化压缩目标文件
2. 打开二进制文件，把下面这些特征全都置零：
   - 节表名 `.UPX0` / `.UPX1` / `.UPX2` → 伪造成 `.text` / `.rdata` / `.rsrc`
   - 魔数 `UPX!`
   - 散落在文件里的 `UPX0` `UPX1` `UPX2` 字符串
   - 信息字符串 `This file is packed with the UPX ...`
3. 校验一遍确认特征已清干净

## 依赖

- Python 3.x（纯标准库，不需要装任何第三方包）
- upx 已经设为当前操作系统环境变量

## 用法

```bash
# 直接处理原文件（原地修改）
python UPX-Decoflator.py payload.exe

# 输出到指定路径，保留原文件不动
python UPX-Decoflator.py -o C:\out\payload_clean.exe payload.exe

# 批量处理（不支持 -o）
python UPX-Decoflator.py payload.exe loader.dll beacon.bin
```

## 示例输出

```
[*] Processing: payload.exe (384 KB)
  [1] Running upx --best ...
  [+] UPX done: 384 KB -> 112 KB (29%)
  [2] Stripping UPX signatures ...
  [+] 12 signatures stripped
  [+] Clean! No UPX signatures remain
  [+] Final size: 112 KB
```

如果文件已经加过壳：

```
[*] Processing: beacon.dll (256 KB)
  [1] Running upx --best ...
  [i] File already packed by UPX, skipping compression
  [2] Stripping UPX signatures ...
  [+] 8 signatures stripped
  [+] Clean! No UPX signatures remain
  [+] Final size: 256 KB
```

## 注意事项

- 不加 `-o` 时直接原地修改文件，不会备份。有需要的话先自己留一份副本，或者用 `-o` 输出到新路径。

- 剥离特征只是过静态查杀的手段之一，不保证免杀效果，实际环境里可能还需要配合其他方式。

## 免责声明

本工具仅供安全研究、授权测试及学习用途。使用者应遵守当地法律法规，在获得明确授权的前提下使用。作者不对任何滥用、非法使用或由此产生的后果承担责任。
