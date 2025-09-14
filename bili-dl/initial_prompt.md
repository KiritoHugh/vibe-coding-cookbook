我要开发一个 GUI 的程序来用 you-get 做视频的下载。

如果是仅仅获得信息：
    you-get -i https://www.bilibili.com/video/BV1p2wLeyEf9 -c "/Users/qiqizhou/Library/Application Support/Firefox/Profiles/hpv7fq1b.default-release/cookies.sqlite"
    展示其输出。
如果是 不是 playlist 的下载:
    cd 到 专辑名（文件夹名）
    you-get --format=dash-flv720-AVC https://www.bilibili.com/video/BV1p2wLeyEf9 -c "/Users/qiqizhou/Library/Application Support/Firefox/Profiles/hpv7fq1b.default-release/cookies.sqlite"
如果是 playlist 的下载:
    cd 到 专辑名（文件夹名）
    you-get --format=dash-flv720-AVC --playlist https://www.bilibili.com/video/BV1p2wLeyEf9 -c "/Users/qiqizhou/Library/Application Support/Firefox/Profiles/hpv7fq1b.default-release/cookies.sqlite"



输入：
- video id : BV1hx4y1t721
- 视频地址 : https://www.bilibili.com/video/BV1hx4y1t721/?vd_source=7a7289c95b87c1a3ad0f882e30b08381
- 是否是 playlist : 一个勾选的框
- 专辑名（文件夹名） : 一个输入框, 默认为当前时间

输出框展示输出信息


---------------

