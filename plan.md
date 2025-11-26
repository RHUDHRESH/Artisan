001. Phase 1 - Goals and success criteria.
002. Success criterion: flight check flags missing web search as blocking.
003. Success criterion: supply search returns actionable message when key missing.
004. Success criterion: supply search returns real results when key present.
005. Success criterion: no silent empty lists from agents.
006. Success criterion: keep cloud-first default intact.
007. Success criterion: local-only path still works with Ollama when configured.
008. Success criterion: UI surfaces setup guidance for search keys.
009. Success criterion: tests cover no-key path and healthy path.
010. Success criterion: docs updated with steps.
011. Non-goal: adding synthetic data.
012. Non-goal: changing model defaults beyond needed.
013. Constraints: stay ASCII, no destructive git commands.
014. Constraint: approval policy never; work within sandbox full access.
015. Constraint: keep existing user changes untouched.
016. Phase 2 - Environment and prerequisites.
017. Record current .env.example values for search keys.
018. Check actual .env presence for keys without exposing secrets.
019. Identify running backend/ frontend versions.
020. Confirm Python 3.9+ available via `python --version`.
021. Confirm node 18+ via `node --version`.
022. Verify `data/` write permissions for Chroma and SQLite.
023. Verify outbound HTTPS allowed for Tavily/SerpAPI.
024. Note network access enabled per environment context.
025. Note sandbox mode danger-full-access allows full fs.
026. Confirm web server ports 8000/3000 free.
027. Identify logging location (uvicorn logs).
028. Confirm test runner available (pytest).
029. Confirm npm for frontend tests.
030. Check existing plan.md replaced by new version.
031. Phase 3 - Reproduce failure.
032. Start backend locally using existing commands (if not already).
033. Hit `GET /health/flight-check` via curl/httpie to capture JSON.
034. Observe `web_search` status and action_items.
035. Attempt supply search flow via API (agents route) with sample payload.
036. Capture backend logs for scraper warnings.
037. Check if response has empty suppliers array.
038. Note any error codes or messages.
039. Reproduce via frontend (if running) by performing supply search UI.
040. Capture frontend console errors.
041. Confirm if production-gate shows flight check results.
042. Verify WebSocket events for search_progress absence.
043. Check vector store status in flight check.
044. Check tool_database status in flight check.
045. Record timestamped reproduction steps.
046. Save sample request/response for comparison after fix.
047. Verify if SerpAPI fallback also missing keys in report.
048. Confirm Tavily key absence is the root cause.
049. Note whether llm_providers status is healthy.
050. Check any exceptions thrown by `OllamaClient.health_check`.
051. Observe action_items list to ensure messages present.
052. Identify any tracebacks in server log.
053. Confirm agents still returning HTTP 200 with empty data.
054. Confirm front-end displays "nothing found" rather than actionable guidance.
055. Note latency of requests to measure improvements later.
056. Verify if state stored to Chroma or Local JSON unaffected.
057. Confirm event scout/growth marketer behave similarly.
058. Identify if caching influences result count.
059. Validate no auth or rate limiting interfering.
060. Summarize reproduction outcome.
061. Phase 4 - Config and env inspection.
062. Inspect `.env.example` to align docs.
063. Check `.env` for search keys presence (without printing values).
064. Ensure `LLM_PROVIDER` default matches docs (groq).
065. Verify `CHROMA_DB_PATH` path correctness.
066. Verify `SUPABASE_URL`/`KEY` presence or absence.
067. Verify `BACKEND_URL` aligns with frontend env vars.
068. Confirm `NEXT_PUBLIC_API_URL`/`WS_URL` reflect backend URL.
069. Ensure `CORS_ORIGINS` matches frontend origin.
070. Check Redis URL used for memory/state.
071. Ensure `LOG_LEVEL` set to INFO for debugging.
072. Inspect `backend/config.py` overrides from env.
073. Ensure `settings.llm_provider` falls back when unspecified.
074. Note `REASONING_MODEL`/`FAST_MODEL` defaults.
075. Confirm `embedding_model` matches constants.
076. Evaluate whether `OPENROUTER`/`GEMINI` keys are optional.
077. Confirm `FlightCheck` uses settings for environment data.
078. Identify any duplication between constants and config.
079. Confirm `web_scraper` reads `tavily_api_key` and `serpapi_key`.
080. Note any plan to disable fallback to SerpAPI when not configured.
081. Evaluate `production-gate` component behavior on missing keys.
082. Ensure `frontend` uses `buildApiUrl` for requests.
083. Check `frontend/components/production-gate.tsx` for error state UI.
084. Identify if `useEffect` handles error responses gracefully.
085. Review `backend/api/routes/search.py` if used.
086. Confirm `WebScraperService` log statements visible.
087. Inspect `backend/core/ollama_client.py` health check for exception cases.
088. Ensure `flight_check` returns actionable suggestions.
089. Confirm doc files align with env defaults.
090. List any config drift to correct.
091. Phase 5 - Backend diagnostics and instrumentation tasks.
092. Add verbose logging in scraper when keys missing.
093. Ensure logs include provider, query, and reason for skip.
094. Instrument Supply Hunter to capture search provider used.
095. Instrument Supply Hunter to capture failure reasons per query.
096. Add metrics counters for missing-key occurrences.
097. Ensure `FlightCheck` enumerates impacts clearly.
098. Validate `FlightCheck._check_web_search` suggestion accuracy.
099. Confirm `FlightCheck` statuses: healthy/warning/unhealthy mapped properly.
100. Add action_item entries for missing keys as blocking.
101. Ensure `FlightCheck` returns HTTP 200 with diagnostics.
102. Consider adding `overall_status` degrade for missing web search.
103. Log path to `.env` being read (without values).
104. Validate `OllamaClient.health_check` handles absence of cloud keys gracefully.
105. Add debug log when `OllamaClient` chooses provider.
106. Confirm `VectorStore` path created and accessible.
107. Ensure `ToolDatabaseManager` handles missing data dir gracefully.
108. Add small docstring clarifications if confusing.
109. Evaluate concurrency of `asyncio.gather` in flight check for error propagation.
110. Add try/except wrappers to avoid uncaught exceptions in checks.
111. Ensure `flight_check` includes `timestamp` in ISO format.
112. Validate `action_items` includes component, status, suggestion.
113. Confirm logging not overly verbose in production.
114. Add structured logging for missing search keys.
115. Confirm `web_scraper.search` returns meaningful object when failing.
116. Add typed return for error cases (e.g., {"error":...}).
117. Ensure error objects flow up to agents.
118. Verify `SupplyHunterAgent.analyze` handles error object gracefully.
119. Add guard to halt verification when search error.
120. Add user-friendly message included in execution logs.
121. Ensure agent summary counts reflect errors (not zero results).
122. Prevent agent from misreporting zero suppliers when key missing.
123. Add fallback message for regional search when skipped.
124. Validate `scraper.search_logs` capture failure.
125. Ensure no unbounded retries on missing keys.
126. Add timeout handling for Tavily calls.
127. Add clear separation of concerns for network vs auth errors.
128. Introduce typed dataclasses? (maybe not necessary).
129. Keep code changes minimal but explicit.
130. Document new log fields in monitoring guide.
131. Consider returning HTTP 503 for missing keys? (decide).
132. Possibly add `health/flight-check` severity to degrade `overall_status`.
133. Ensure not to expose secret values in responses.
134. Mask API key previews to 6 chars only.
135. Ensure no blocking operations on event loop.
136. Confirm `requests` fallback thread usage safe.
137. Validate `httpx` fallback when installed optional.
138. Add tests for `_check_web_search` statuses.
139. Add tests for `scraper.search` missing-key branch.
140. Add tests for `SupplyHunterAgent` handling missing-key result.
141. Phase 6 - Backend fixes implementation steps.
142. Update `FlightCheck._check_web_search` to mark status `unhealthy` with blocker flag when no key.
143. Include `impacts` list showing affected agents (Supply Hunter, Growth, Event).
144. Add `suggestion` with exact env var names and sample values.
145. Ensure `overall_status` becomes `degraded` when web_search unhealthy.
146. Update `web_scraper.search` to return dict `{"error": "no_api_key", "message": "..."}`.
147. Add typed result: list or error dict; document expectation.
148. Modify `SupplyHunterAgent.analyze` to detect error dict and short-circuit.
149. Add `execution_logs` entry explaining missing API key and next steps.
150. Return response with `total_suppliers_found`=0 and `error` message explicit.
151. Update `WebScraperService.search_logs` to include failure entries.
152. Add class property to set `required=True` for keys? Evaluate.
153. Add explicit check on init to warn on missing keys once.
154. In `_search_tavily`, handle HTTP errors with structured error dict.
155. In `_search_serpapi`, same structured error dict.
156. Update agent verification loop to skip when search error.
157. Add type hints to functions returning mixed data.
158. Update docstring for `scrape_page` to note WebSocket broadcast optional.
159. Add error propagation to front-end via API response.
160. Ensure API route `search` returns error code when search fails.
161. Decide on HTTP status: 400 for missing config; update accordingly.
162. Update `backend/api/routes/search.py` to pass through error message.
163. Ensure websockets broadcast failure state if available.
164. Update `monitoring` to capture missing key events as warnings.
165. Update constants if new messages needed.
166. Add `BLOCKING_MISSING_SEARCH_KEY` message constant? optional.
167. Keep backward compatibility with previous consumers.
168. Avoid breaking changes in response schema unless documented.
169. Add new response field `action_required` boolean if config missing.
170. Update Pydantic models if needed.
171. Ensure `health/flight-check` remains fast despite extra checks.
172. Avoid hitting Tavily if key missing; return early.
173. Add support for environment variable validation at startup.
174. Optionally fail startup if key required? choose not to for local mode.
175. Document behavior in README/TROUBLESHOOTING.
176. Add sample error JSON to docs.
177. Update logging to include correlation IDs if available.
178. Ensure `uvicorn` log level remains manageable.
179. Re-run mypy? (if available) to catch type issues.
180. Ensure dependencies not added unless needed.
181. Keep runtime dependencies same (no new libs).
182. Add unit tests under `backend/tests` for new branches.
183. Update `backend/tests/test_complete_system.py` if necessary.
184. Mock Tavily calls to avoid network in tests.
185. Use `pytest` fixtures for settings manipulation.
186. Reset env vars after tests to avoid bleed.
187. Ensure tests run in CI with no keys present.
188. Update `CICD_SETUP.md` if tests rely on env.
189. Add skip markers for network tests if no key set.
190. Validate import paths correct.
191. Ensure concurrency with `asyncio` tests properly awaited.
192. Add coverage for `FlightCheck._finalize` with unhealthy web search.
193. Add regression test for `overall_status` degrade.
194. Ensure JSON serialization safe for new fields.
195. Add minimal docstring on new error dict structure.
196. Validate no circular imports introduced.
197. Run `python -m compileall backend`? optional.
198. Ensure `__all__` unaffected.
199. Keep code comments succinct per guidelines.
200. Prepare for frontend integration.
201. Phase 7 - Frontend handling steps.
202. Update `frontend/components/production-gate.tsx` to surface web_search blocking status.
203. Add UI banner for missing search API key with steps to set `.env`.
204. Show preview of flight-check `action_items`.
205. Add CTA linking to README section for keys.
206. Disable search buttons when flight-check reports blocking web search.
207. Provide copy-paste env snippets in UI text.
208. Show retry button to rerun flight-check after .env change.
209. Handle backend error responses from agents gracefully.
210. If API returns `error: no_api_key`, show modal/toast with guidance.
211. Ensure loading spinners handle early failure path.
212. Update typing in component to include `action_required` field.
213. Adjust `buildApiUrl` usage to include correct base.
214. Ensure WebSocket listener handles failure broadcasts.
215. Update CSS for warning states distinct from generic empty state.
216. Add tests for component states (if test infra present).
217. Verify mobile view displays guidance properly.
218. Avoid leaking any key values in UI.
219. Ensure text localizes? not needed but keep simple.
220. Confirm UI matches existing design language.
221. Add aria labels for warnings.
222. Ensure no infinite retry loops on fetch failures.
223. Provide link to plan.md? maybe not in UI.
224. Add fallback message when backend unreachable.
225. Ensure hydration warnings avoided in Next.js.
226. Update any `useEffect` dependencies to prevent extra calls.
227. Confirm component cleans up pending fetch on unmount.
228. Add simple icon (emoji) for warning? consistent design.
229. Test with API returning HTTP 400 and JSON error.
230. Test with flight-check returning degraded state.
231. Test with healthy state to ensure normal flow unchanged.
232. Update docs in frontend README if needed.
233. Confirm lint passes (ESLint).
234. Confirm TypeScript types updated if API schema changed.
235. Add storybook story? only if available, likely skip.
236. Make sure `production-gate` still renders in production build.
237. Ensure `NEXT_PUBLIC_API_URL` used for fetch matches backend.
238. Add helper to render action items list.
239. Ensure no blocking SSR errors due to fetch.
240. Keep UI text concise and actionable.
241. Phase 8 - Testing strategy and cases.
242. Backend unit test: FlightCheck web_search no key returns unhealthy + action_items.
243. Backend unit test: FlightCheck with Tavily key set returns healthy.
244. Backend unit test: web_scraper.search returns error dict when keys missing.
245. Backend unit test: SupplyHunterAgent returns error message and zero suppliers on missing key.
246. Backend unit test: SupplyHunterAgent normalizes error into execution_logs.
247. Backend unit test: API route for search returns 400 with error when missing key.
248. Backend unit test: API route for search returns 200 with data when key mocked.
249. Backend unit test: Logging not exposing keys.
250. Backend unit test: overall_status degraded when web_search unhealthy.
251. Backend unit test: action_items length >0 when missing key.
252. Backend unit test: scraper search logs include provider and status.
253. Backend unit test: serpapi fallback handled when tavily missing but serp present.
254. Backend unit test: duplicate detection unaffected.
255. Backend unit test: scraper handles HTTP error codes gracefully.
256. Backend unit test: vector_store unaffected by missing search keys.
257. Backend unit test: tool_database unaffected by missing search keys.
258. Backend unit test: ollama health check failure does not hide web search status.
259. Backend unit test: httpx absence fallback to requests still works.
260. Backend async test: `asyncio.gather` handles raised exceptions.
261. Frontend test: production-gate renders blocking banner when flight-check degraded due to web_search.
262. Frontend test: production-gate renders healthy state properly.
263. Frontend test: agent UI shows actionable message on backend error `no_api_key`.
264. Frontend test: retry button reruns fetch and updates state.
265. Frontend test: loading state cleared on error.
266. Frontend test: action items list renders without crash.
267. Frontend test: handles missing timestamp gracefully.
268. Manual test: set Tavily key and perform supply search returns results.
269. Manual test: remove key and confirm error guidance appears.
270. Manual test: WebSocket still works for other components.
271. Manual test: Cloud run not required for local tests.
272. Manual test: README links open correctly.
273. Manual test: .env.example matches code behavior.
274. Regression test: ensure environment without Supabase still works.
275. Regression test: ensure CORS config still allows frontend origin.
276. Regression test: ensure backend startup unaffected by new checks.
277. Regression test: ensure CLI scripts unaffected.
278. Performance test: flight-check remains fast (<2s).
279. Performance test: supply search error path quick (<1s).
280. Logging test: verify log lines not excessive.
281. Security test: ensure no secrets printed in responses/logs.
282. Security test: ensure no injection risk in error handling.
283. Deployment test: confirm Cloud Run health check still passes when keys provided.
284. Deployment test: confirm Vercel frontend uses new messaging.
285. Cross-browser test: Chrome/Edge for new UI warning.
286. Accessibility test: warning text screen-reader friendly.
287. Clean-up test: ensure temporary files not created.
288. Snapshot test: none needed unless UI diff baseline.
289. Lint test: run `pytest` and `npm test`/`lint` if available.
290. Coverage review: ensure new branches covered.
291. Phase 9 - Validation and rollout.
292. Re-run `GET /health/flight-check` post-fix; expect web_search healthy when key present.
293. Capture JSON and attach to notes.
294. Re-run supply search with key missing; expect 400/clear message.
295. Re-run supply search with key present; expect non-empty suppliers.
296. Verify frontend shows guidance when missing key.
297. Verify frontend shows results when key set.
298. Verify action items list empties when healthy.
299. Document steps in TROUBLESHOOTING for missing keys.
300. Update README note about required search key for real data.
301. Update HOW_TO_USE to point to new UI guidance.
302. Update QUICK_START if needed to emphasize key requirement.
303. Add change log entry summarizing fixes.
304. Prepare commit message (if requested) summarizing changes.
305. Tag plan completion in plan.md.
306. Ensure all tests passing locally.
307. If CI available, check pipeline status.
308. Provide user summary and next steps.
309. Leave instructions to remove temporary artifacts (none expected).
310. Confirm no sensitive data stored in repo.
311. Phase 10 - Risks and contingencies.
312. Risk: Tavily outage causes degraded state; mitigation: clear messaging and SerpAPI fallback if configured.
313. Risk: Users without internet cannot get suppliers; mitigation: explain requirement and local-only limitations.
314. Risk: Frontend warning could be intrusive; mitigation: design concise banner.
315. Risk: Additional tests increase runtime; mitigation: keep tests small and mock network.
316. Risk: API schema change could break clients; mitigation: maintain backward compatibility and document error fields.
317. Risk: Logging volume too high; mitigation: guard with log level.
318. Risk: Permission issues writing data dir; mitigation: include guidance in action items.
319. Risk: Typos in .env cause confusion; mitigation: add validation and explicit key names in messages.
320. Risk: Time overruns; mitigation: prioritize backend fix, then UI, then tests.
321. Phase 11 - Frontend UX reliability for agents (WebSocket + progress)
322. Add explicit connection status badge in AgentView (connected / reconnecting / failed) tied to ws events, not guessed.
323. When WebSocket errors, show a non-blocking banner but keep HTTP flow usable; do not claim “not connected” if HTTP completes.
324. Ensure ws reconnect timer clears on unmount and disables retries after N attempts to avoid loops.
325. Gate startSearch when ws is connecting? No—allow search but warn that live logs may be missing.
326. Add timeout/guard: if no progress logs within 30s and HTTP still pending, surface “backend still working” vs “stuck” with retry CTA.
327. Map backend 400 error payloads (missing_api_key) to a clear UI card with steps to add TAVILY_API_KEY/SERPAPI_KEY.
328. If backend returns error, stop spinner, append log entry, and avoid “searching...” lingering.
329. Add a “Stop/Reset” button to clear isSearching/searchLogs/results for stuck states.
330. Normalize results: if backend returns empty results with no error, show “No items found” instead of infinite searching.
331. Update production-gate flight check view to highlight web_search blocking and link to env snippet.
332. Add lightweight front-end tests (if infra) for connection status rendering and error card mapping.
