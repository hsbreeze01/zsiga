我需要亲自验证这个 proposal 的核心前提——`daemon.py` 中是否真的存在这些 HTTP 路由。Scout 的分析指出没有找到任何 Web 框架，这让我高度怀疑。让我直接看代码。

<tool_call_tool>
{"name": "bash", "arguments": {"command": "cd /home/user && grep -n 'status\\.json\\|metrics\\.json\\|current\\.json\\|/api/\\|do_GET\\|BaseHTTPRequestHandler\\|http\\.server\\|RequestHandler\\|def _serve\\|path.*json' zsiga/daemon.py | head -40"}}
</tool_call_tool>
<tool_result>
244:    def _serve_dashboard(self):
289:        return json.dumps({"daemon": daemon, "queue": queue}, ensure_ascii=False, indent=2)
</tool_result>

<tool_call_tool>
{"name": "bash", "arguments": {"command": "cd /home/user && grep -n 'route\\|/api\\|endpoint\\|GET\\|POST\\|request\\|handler\\|listen\\|serve\\|HTTP\\|url\\|path.*==' zsiga/daemon.py | head -40"}}
</tool_call_tool>
<tool_result>
244:    def _serve_dashboard(self):
271:            print(f"Daemon listening on http://localhost:{port}")
278:                if path == "/api/status.json":
281:                elif path == "/api/metrics.json":
284:                elif path == "/api/current.json":
287:                elif path == "/api/health":
289:                elif path == "/api/proposal-stats":
293:                elif path == "/":
295:                elif path == "/dashboard":
</tool_result>

<tool_result>

</tool_result>

<tool_call_tool>
{"name": "bash", "arguments": {"command": "cd /home/user && sed -n '260,310p' zsiga/daemon.py"}}
</tool_call_tool>
<tool_result>
260        self._lock_path = lock_path
261        self._lock_fd = None
262
263    def start(self, port: int = 58175):
264        import http.server
265
266        class _Handler(http.server.BaseHTTPRequestHandler):
267            def do_GET(self):
268                path = self.path.split("?")[0]
269
270                if False:
271                    pass
272                elif path == "/api/status.json":
273                    self._send_json(200, self.server.daemon._build_status_json())
274                elif path == "/api/metrics.json":
275                    self._send_json(200, self.server.daemon._build_metrics_json())
276                elif path == "/api/current.json":
277                    self._send_json(200, self.server.daemon._build_current_json())
278                elif path == "/api/health":
279                    self._send_json(200, self._daemon_health())
280                elif path == "/api/proposal-stats":
281                    self._send_json(200, self.server.daemon._build_proposal_stats_json())
282                elif path == "/":
283                    self._send_json(200, {"status": "running"})
284                elif path == "/":
285                    self._send_text(200, self.server.daemon._serve_dashboard())
286                elif path == "/dashboard":
287                    self._send_text(200, self.server.daemon._serve_dashboard())
288                else:
289                    self._send_json(404, {"error": "not found"})
290
291        _Handler._send_json = _send_json
292        _Handler._send_text = _send_text
293        _Handler._daemon_health = _daemon_health
294
295        httpd = http.server.HTTPServer(("127.0.0.1", port), _Handler)
296        httpd.daemon = self
297        self._httpd = httpd
298        self._httpd.serve_forever()
299
</tool_result>

现在我掌握了真相。让我做出判断。

## Verdict: ACCEPT

## 我的判断

我差点被 Scout 的分析误导了。Scout 搜遍了 Flask、FastAPI、Django 却一无所获，就断言"不存在 HTTP 路由"——但真相是 daemon.py 用的是 Python 标准库 `http.server.BaseHTTPRequestHandler`，用最朴素的 `if/elif` 字符串匹配实现路由。我亲眼看到了第 272-289 行：`/api/status.json`、`/api/metrics.json`、`/api/current.json`、`/api/health`、`/api/proposal-stats` 全部白纸黑字存在。

这个 proposal 的诊断完全准确：三个带 `.json` 后缀的路由和两个不带后缀的路由确实不一致。改法也很清晰——在同一个 `_Handler` 类里重命名路由分支、加几个 `elif` 做 301 重定向。单文件变更、零新依赖、向后兼容。唯一值得注意的是第 282-285 行有个重复的 `elif path == "/":` 分支（一个返回 JSON，一个返回 dashboard），这是个现成的 bug，但不在本 proposal 范围内，可以先记下。

## 评分详情
- **可行性: 2/2** — 目标文件 `zsiga/daemon.py` 存在（690行），三个 `.json` 路由在第 272、274、276 行逐字确认存在。使用 stdlib `http.server`，改路由字符串 + 加重定向分支完全可行。
- **可执行性: 2/2** — 变更文件明确（`zsiga/daemon.py` 单文件），具体到行号级别的修改路径：把 `/api/status.json` 改成 `/api/status`，新增旧的 `.json` 路径返回 301。验收标准用 `curl` 命令逐条列出，清晰无歧义。
- **能力匹配: 1/2** — 无同类历史记录，按规则给 1。
- **历史风险: 2/2** — 无相关失败记录，无 auto-generated 标记，无循环风险。
- **范围合理性: 2/2** — 范围精确定位：单文件、5 个路由端点、只改命名加重定向。明确声明 dashboard UI 和新端点不在范围内。不涉及 pipeline 自身代码。
- **总分: 9/10**

## 疑虑
不适用（ACCEPT）。但记录一个发现：`daemon.py` 第 282-285 行存在重复的 `elif path == "/":` 分支，前一个返回 `{"status": "running"}` JSON，后一个返回 dashboard HTML。由于 `elif` 链的特性，第二个永远不会执行——这是一个现成 bug，建议作为后续 proposal 处理。
