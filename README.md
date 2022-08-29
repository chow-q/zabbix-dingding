# zabbix-dingding  

功能：  

    zabbix钉钉告警脚本附历史监控图；  
    
原理：  

    通过告警事件id获取当前监控项历史监控图像，上传到cos  
    
配置：   

    zabbix告警媒介要增加参数：{ITEM.ID}  

示例:  
![Alt text](https://raw.githubusercontent.com/chow-q/zabbix-dingding/main/demo.png)
    
