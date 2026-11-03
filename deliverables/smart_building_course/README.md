# 集成语音感知与云平台的多任务智能楼宇控制系统

2026年11月3日依据新技术文档与钱图、陆子芃、孙建庚实际分工修订。应用背景为智能楼宇单房间教学场景，正文沿用课程指导书的14章结构。

- [下载Word修订稿](Smart_Building_Course_Paper.docx?raw=true)
- [查看PDF（21页）](Smart_Building_Course_Paper.pdf)
- [下载论文、图源及补充清单材料包](Smart_Building_Paper_Package.zip?raw=true)
- [查看尚需补充与核验的信息](Remaining_Information.md)
- [查看技术文档所附原理图原图](System_Schematic_From_Technical_Document.png)

已纳入DHT11、MQ-2、GL5516、OLED、ESP8266、SU-03T的文档接线，三人实际职责及模块接口流程。钱图与陆子芃共同负责OLED菜单相关工作，报告保留共同分工。

主控已确认STM32F103C8T6，Wi-Fi属于ESP8266系列。Wi-Fi具体模块及图文收发线、电机“直连”与驱动图的差异、PWMA/STBY、电机供电和MQ-2 ADC输入范围等仍待实物核验。若电机电源线确实直接接GPIO，应先断电并使用匹配驱动级。

现稿使用原理图和功能说明，不宣称已复现实物、Proteus或PCB工程，不将旧温室的53项测试用于本楼宇系统。当前原理图带嘉立创EDA标识，不能认定为已提交Altium源工程。

Word打开后Ctrl+A、F9更新目录。PDF使用环境字体替代预览；最终严格字体版请在装有宋体、黑体和Times New Roman的Word环境中导出。学号、课程信息、实际源工程与原始量化测试记录仍需补充。
