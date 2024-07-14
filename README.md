# Telegram 一个超级简单的TG群组抽奖机器人，她是大波小秘书，她的名字叫Sola

这是一个简单的 Telegram 抽奖机器人，允许用户通过发送消息参与抽奖，并在指定条件达成后随机选择获胜者。

## 准备工作
1. 创建一个tg机器人
2. 一个独立的vps（自己完全控制，并注意避免泄露自己的机器人token）

## 安装

## 安装python3
1.大多数 Linux 发行版都预装了 Python。您可以通过以下命令检查版本：
```
python --version
```
2.如果您的系统没有 Python，或者您需要特定版本，则可以使用发行版的包管理器进行安装。例如，在 Ubuntu 上，您可以使用以下命令：
```
sudo apt install python3
```
3.安装pip
```
sudo apt-get install python3-pip
```
4.安装python-telegram-bot包
```
pip install python-telegram-bot --upgrade
```
5.安装python-telegram-bot的依赖
```
pip install "python-telegram-bot[job-queue]"
```

## 下载bot.py并在代码242行修改对应的机器人token

```
application = Application.builder().token("你的机器人token").build()
```

## 使用

1. 启动机器人：

    ```bash
    python bot.py
    ```
    ## 常驻后台运行
    ```bash
    nohup python bot.py &
    ```
2. 在 Telegram 群组添加你的机器人然后与机器人聊天，发送 `/start` 命令以开始使用。

3. 管理员可以通过发送 `/create <奖品名称> <奖品数量> <参与口令> <抽奖条件>` 创建抽奖活动。

4. 用户通过发送口令参与抽奖活动。

## 命令

- `/start`：开始与机器人的对话
- `/create <奖品名称> <奖品数量> <参与口令> <抽奖条件>`：创建抽奖活动（仅管理员可用）
- `/join <口令>`：通过口令参与抽奖活动
- `/cancel`：取消当前的抽奖活动（仅管理员可用）

---

## 许可证

此项目使用 MIT 许可证。请参阅 [LICENSE](LICENSE) 文件了解更多信息。


