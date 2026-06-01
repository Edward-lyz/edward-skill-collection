---
name: python-dev-standards
description: |
  Python 代码开发与审查规范。适用于编写、重构、review Python 代码，
  重点约束可读性、错误处理、类型、测试、性能、装饰器使用。
  触发词：python 规范、Python 开发规范、python review、py code style、
  python decorator、Python 重构规范。
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - MultiEdit
  - Write
  - Bash
  - Agent
---

# Python Dev Standards — Python 开发规范

目标：写直接、清晰、可验证的 Python 代码。失败显式暴露，行为由代码
本身解释，不靠隐式兜底、过度抽象或测试造假维持表面正确。

## 执行流程

1. 先读相邻代码：命名、错误处理、类型风格、测试风格必须沿用现有结构。
2. 明确公共边界：只在外部输入入口做完整校验，内部代码不扩散防御。
3. 先写直达实现：不用 registry、strategy、adapter、base class 预留假想需求。
4. 修改后运行最小真实验证：单测、类型检查、lint 或可复现脚本。
5. review 时只指出真实问题：给出文件、行号、风险、直接改法。

## 常见必须避免

### Hidden fallback

- 禁止 `except` 后返回空列表、空 dict、`None`、零值、mock 值。
- 禁止主实现失败后静默切换旧实现、慢实现、近似实现。
- 禁止缺配置、缺依赖、缺数据时跳过核心逻辑。
- 禁止用 env flag 绕过 bug，除非用户明确要求兼容开关。
- 允许降级时，必须让调用方看到明确状态或异常，不能伪装成功。

### 异常处理

- 禁止裸 `except:`，除进程边界清理逻辑外禁止宽泛 `except Exception`。
- 捕获异常必须处理具体类型，并保留上下文：`raise ... from exc`。
- 不要把异常变成布尔值或空结果。调用方需要知道失败原因。
- `assert` 只拦截不可能发生的内部状态，不用于用户输入校验。
- `asyncio.CancelledError` 必须继续传播，不能被宽泛捕获吞掉。
- 禁止嵌套 `try`/`except`。需要二次处理时，拆成清晰的顺序步骤或让异常上抛。
- `try` 块必须尽量小，只包可能抛出目标异常的语句。
- 不要把整个函数体包进 `try`。这会模糊失败位置并吞掉未知错误。
- 不要在 `except` 里再写 `try`。清理逻辑用 `finally` 或 context manager。
- 不要在 `finally` 里 `return`、`break`、`continue`，避免覆盖原始异常。
- 需要区分成功后逻辑时，用 `try`/`except`/`else`，不要把成功路径塞进 `try`。
- `KeyboardInterrupt`、`SystemExit`、`GeneratorExit` 不应被业务代码捕获。
- 不要用异常做普通分支控制。可预期分支应显式判断。

#### 正确 `try`/`except` 模式

```python
try:
    payload = json.loads(raw_payload)
except json.JSONDecodeError as exc:
    raise ValueError(f"invalid request payload: {source_name}") from exc

process_payload(payload)
```

```python
try:
    response = await client.fetch(request)
except asyncio.CancelledError:
    raise
except TimeoutError as exc:
    raise UpstreamTimeout(upstream_name) from exc
else:
    validate_response(response)
```

#### 错误 `try`/`except` 模式

```python
try:
    config = load_config(path)
    client = create_client(config)
    data = client.fetch()
    return parse_data(data)
except Exception:
    return {}
```

```python
try:
    try:
        value = parse(raw_value)
    except ValueError:
        value = 0
except Exception:
    log.warning("parse failed")
```

### 函数与抽象

- 禁止 1 到 3 行且只调用一次的机械 helper。
- 重复少于 3 次默认不抽公共函数。
- 禁止只转调、只包 `if`、只返回字段的 helper。
- 禁止为了缩短主函数而拆函数；拆分必须降低理解成本。
- 禁止 bool flag 控制两套业务语义。拆成两个命名清楚的函数。
- 类只在需要封装状态或稳定协议时引入；普通流程优先函数。

### 嵌套深度

- 禁止过深嵌套。函数内缩进超过 3 层必须优先改写。
- 优先用 guard clause、early return、early continue 降低嵌套。
- 循环内复杂 `if` 应先过滤非法分支，再处理主路径。
- `if`/`for`/`with`/`try` 叠加时，先判断是否能提前退出或拆成明确阶段。
- 不要为了降低缩进机械抽 1 到 3 行 helper；改写控制流优先。
- 多层业务分支应显式命名中间状态，而不是继续增加缩进。

#### 降低嵌套示例

```python
for record in records:
    if not record.enabled:
        continue
    if record.expired_at <= now:
        continue

    active_records.append(record)
```

### 命名与可读性

- 禁止业务代码中新增以 `_` 开头的函数、类名、变量名。
- 禁止用 `_` 或 `_name` 表示私有、临时或未使用；改用清晰业务名，
  或重写控制流避免绑定无用值。
- 禁止类内部状态使用 `self._name`、`cls._name` 或 `_ClassName` 风格。
- 仅 Python 协议强制的标准 dunder 方法可保留，例如 `__init__`、
  `__repr__`；不要自造 dunder 名或 private-like 名。
- 避免 `data`、`tmp`、`obj`、`item`、`result`、`handle` 等含糊名。
- 名字表达业务含义，不表达临时实现细节。
- 变量靠近使用处声明，一个变量只承载一个语义。
- 注释解释为什么，不翻译代码做什么。

### 类型与数据结构

- 公共函数必须写参数和返回类型；内部复杂函数也要写类型。
- `Optional[T]` 只在 `None` 是真实业务状态时使用。
- 不用 `Any` 逃避建模；必要时把 `Any` 限制在外部边界。
- 固定结构用 `dataclass`、`TypedDict` 或已有模型，不用裸 dict 传全局。
- 不要返回可变内部状态；需要暴露时返回副本或不可变视图。
- 不要使用可变默认参数。用 `None` 表示未提供，再显式创建。

### IO、路径、时间

- 文件路径优先用 `pathlib.Path`，文本 IO 显式指定 `encoding`。
- 库代码禁止 import 时执行 IO、网络请求、进程启动、环境修改。
- 写文件需考虑原子性；重要产物先写临时文件再替换。
- 时间必须使用 timezone-aware 值；默认用 UTC。
- 不用 float 表示金额、精确计数或可审计数值。

### Async 与并发

- async 函数内禁止阻塞 IO、`time.sleep`、CPU 重循环。
- 并发数量必须有上界；不要无限 `gather`。
- 共享状态必须有明确同步；不要靠 GIL 假设线程安全。
- 后台任务必须有生命周期管理，不能 fire-and-forget 后丢失异常。

### 性能

- 热路径避免重复正则编译、重复解析、重复构造大对象。
- 大数据处理优先迭代、流式或批处理，避免一次性读入无界数据。
- 避免隐式 O(n²)：循环内 `list.remove`、字符串拼接、DataFrame append。
- 优化前先建立 baseline；每次只改一个性能假设并验证。

### 测试

- 禁止为了通过测试 fake 行为、跳过真实路径、降低断言强度。
- 测试必须断言具体行为、错误类型、关键消息或可观察副作用。
- 失败用例有价值时保留，先修代码，不删测试。
- mock 只用于外部不可控边界，不 mock 被测核心逻辑。

## 推荐装饰器与使用边界

装饰器只能用于清晰表达语义或消除真实重复。禁止用装饰器隐藏 IO、
重试、缓存、权限、降级等关键行为。

### 标准库优先

- `@dataclass(frozen=True, slots=True)`：不可变值对象。字段少、语义稳定时使用。
- `@dataclass(slots=True)`：轻量状态对象。需要可变状态时明确接受可变性。
- `@functools.lru_cache(maxsize=N)`：纯函数、输入有界、结果不可变时使用。
- `@functools.cache`：仅用于输入空间天然很小且进程级缓存可接受的纯函数。
- `@functools.cached_property`：实例不可变后，惰性计算昂贵且无副作用的属性。
- `@property`：廉价、无副作用、不会失败的派生值。慢操作用显式方法。
- `@classmethod`：命名构造器，例如 `from_config`、`from_path`。
- `@staticmethod`：仅当函数放在类里能表达强业务归属；否则写模块函数。
- `@functools.wraps`：任何自定义装饰器必须使用，保留签名与元数据。
- `@contextlib.contextmanager`：简单资源申请/释放。复杂流程写显式类或函数。
- `@contextlib.asynccontextmanager`：异步资源生命周期，确保异常路径释放资源。
- `@typing.final`：禁止继承的稳定类或禁止 override 的方法。
- `@typing.override`：覆写父类方法时使用。旧 Python 仅在已有依赖时用 `typing_extensions`。
- `@abc.abstractmethod`：已有真实多实现契约时使用；不要为假想扩展创建接口。
- `@functools.total_ordering`：小型值对象补齐比较；热路径手写完整比较方法。
- `@functools.singledispatch`：公共 API 真正需要按类型扩展时使用，不当策略注册表。

### 测试装饰器

- `@pytest.mark.parametrize`：覆盖等价类、边界值、错误路径，避免复制测试函数。
- `@pytest.fixture`：共享真实 setup。fixture 名必须表达业务含义，scope 显式。
- `@pytest.mark.asyncio` 或项目现有 async marker：只用于真实 async 路径。

### 第三方装饰器

- Pydantic `@field_validator`、`@model_validator`：只在外部数据边界做校验。
- Web 框架路由装饰器：只在接口层使用，业务逻辑保持普通函数可测试。
- Retry、cache、permission、metric 装饰器：只有项目已有统一约定时使用，且行为必须可见。

### 装饰器慎用清单

- 不要堆叠多层装饰器导致真实控制流不可见。
- 不要用 `@property` 触发网络、磁盘、数据库或昂贵计算。
- 不要给依赖 `self` 大对象的方法随意加 `lru_cache`，会延长实例生命周期。
- 不要写只用一次的 custom decorator。
- 不要写改变函数签名、吞异常、改返回值语义的装饰器。
- 不要把业务分支藏在 decorator 参数里。

## Review 输出格式

只输出需要修改的问题。格式：

```text
`path/to/file.py:line` — 问题 → 风险 → 直接改法
```

无问题时输出：`未发现 Python 规范问题`。

## 最终检查清单

- 读过相邻代码并沿用风格。
- 没有 hidden fallback。
- 没有过深嵌套，缩进超过 3 层的逻辑已改成直达控制流。
- 没有嵌套 `try`/`except`，异常捕获范围足够小且保留上下文。
- 公共边界有输入校验，内部没有防御式噪声。
- 函数、类名、变量名没有以 `_` 开头的业务标识符。
- 类型表达真实语义，没有滥用 `Any` 或 `Optional`。
- 装饰器表达明确语义，没有隐藏失败、IO、缓存或复杂控制流。
- 测试验证真实行为，未 mock 被测核心逻辑。
