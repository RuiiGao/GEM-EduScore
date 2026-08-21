# GEM-EduScore 公网部署指南

要让评委和访客在没有项目文件、Python 或 API Key 的情况下直接访问，需要把应用部署为公开 Web 服务。推荐使用 Streamlit Community Cloud，因为项目已经采用 Streamlit，并且该平台能直接安装 `requirements.txt`、管理密钥并生成 `streamlit.app` 网址。

## 部署后用户体验

访客只需要打开一个网址：

```text
https://your-gem-eduscore.streamlit.app
```

访客可以上传 MD、TXT、DOCX、含文本层 PDF、PPTX、HTML 或 CSV 材料，也可以输入公开队伍 Wiki 网址，或把文件与 Wiki 合并分析；内置案例仍可直接使用。

## 1. 准备 GitHub 仓库

将整个 `GEM-EduScore` 目录放入一个 GitHub 仓库。必须保留以下内容，因为产品会直接读取现有方法论文档：

```text
GEM-EduScore/
├── Framework/
├── Benchmark/
├── Demo/
└── GEM-EduScore-Product/
    ├── app.py
    └── requirements.txt
```

不要上传 `.streamlit/secrets.toml`、`.env` 或任何真实 API Key。

## 2. 在 Streamlit Community Cloud 创建应用

1. 登录 `share.streamlit.io` 并连接 GitHub。
2. 选择 **Create app**。
3. 选择仓库与分支。
4. Entrypoint 填写：

```text
GEM-EduScore-Product/app.py
```

如果仓库根目录本身就是 `GEM-EduScore-Product`，说明 Framework 和 Benchmark 没有一起部署，当前版本将无法加载 Master Prompt，不建议这样组织。

## 3. 安全配置托管模型

进入 **Advanced settings → Secrets**，参考 `.streamlit/secrets.toml.example` 填写：

```toml
OPENAI_API_KEY = "sk-your-key"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-5-mini"
OPENAI_ENDPOINT = "responses"

GEM_EDUSCORE_MANAGED_API = "true"
GEM_EDUSCORE_ACCESS_CODE = "your-judging-code"
GEM_EDUSCORE_SESSION_LIMIT = "4"
```

密钥必须通过部署平台的 Secrets 功能设置，不能写入 GitHub。

## 4. 展示与费用控制建议

- 正式答辩：设置简短访问码，并把网址制作成二维码。
- 公开展示：可以移除访问码，但应单独设置 API 项目预算和速率限制。
- `GEM_EDUSCORE_SESSION_LIMIT` 只限制单个浏览器会话，不能替代服务端总预算。
- 单项目评估计为 1 次调用；双项目对比需要分别评估两个项目，计为 2 次调用，但横向比较本身不再触发第三次模型调用。
- 不要使用包含敏感个人信息的教育材料进行公开演示。

## 5. 本地与公网入口

- 本机展示：双击 `启动 GEM-EduScore.pyw`。
- 同一局域网：启动器会显示可复制的局域网地址；具体可用性取决于防火墙和网络策略。
- 远程评委与公众：使用部署后获得的 `streamlit.app` 网址。

## 当前尚需人工完成的步骤

创建公网网址需要仓库所有者的 GitHub/Streamlit Cloud 登录权限，以及用于托管调用的 API Key。因此代码可以准备好部署，但不能在没有账户授权的情况下替项目所有者创建正式公网服务。
