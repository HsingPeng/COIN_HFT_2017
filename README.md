# COIN_HFT

## intro

基于数字货币交易所的三角套利实盘程序。

曾在2017年11月份运行良好，200元入场，月收益10w+。2018年1月进入亏损状态，停止运行。

## branch

| branch| intro|
|--|--|
|master|空|
|dev | okex的第一个版本，同步使用条件变量，问题多|
|feature-queue | okex的第二个版本，同步使用队列，还行。（正在使用）|
|feature-quickorder | okex的第三个版本，基于基准货币的交易同时进行，待完成。|
|feature-huobi | huobi的第一个版本，同步等待顺序执行，效果较差。（正在使用）|
|feature-huobi-hedge | huobi的第二个版本，三笔交易同时进行，对冲操作，不完善。|
| feature-okex-wave | okex网格策略，无盈利。|
| feature-binance | binance策略，无盈利。|

有效运作时间最长的是 feature-queue

## 概念解释

这里明确两个概念（自己定的）：

- quickorder 快速交易特指基于基准货币的交易同时进行，以加速交易的策略。
- hedge         对冲交易特指三笔交易同时进行交易，以加速交易的策略。

quickorder需要预先在基准货币，如eth、btc等存放操作资金。

hedge则需要在所有的可能操作的货币中均存放一定量的操作资金。

quickorder 相对于 hedge 的优势在于：

1. 操作资金更可控，更少
2. 盈亏统计更方便
3. 虚拟货币贬值对操作者的影响较小
4. 基准货币贬值可能性较小。

hedge 的优势在于：

1. 更少的操作延迟，可能意味着更大的利润。