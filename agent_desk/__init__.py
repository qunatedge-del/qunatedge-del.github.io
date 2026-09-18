"""agent_desk: 一人交易桌的多代理紙上交易系統。

角色（5 到 8 個，不是 350 個）：
  DataAgent      資料層（K 線、新聞），只在有新資料時發事件
  SentimentAgent 新聞情緒（LLM，事件觸發）
  SignalAgent    訊號層（純量化規則）
  RiskAgent      風控（純程式碼、硬上限、kill switch）
  PaperBroker    執行層（紙上交易 + 人工審核閘門）
  MonitorAgent   監控（規則式告警）
  ReportAgent    日報（LLM，每交易日最多一次）
"""

__version__ = "0.1.0"
