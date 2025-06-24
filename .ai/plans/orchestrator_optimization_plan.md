### **Definitive Plan: Orchestrator Parallelization & Optimization**

**File to be Modified:** `scripts/testnet_orchestrator_hotreload.py`

**High-Level Goal:** Convert the sequential service startup into a parallelized process to minimize total boot time. The core idea is to launch all services at once, then wait for them all to become healthy concurrently.

---

### **Success Criteria**

- **Primary Metric:** Reduce the "cold start" (dependencies not installed) time by at least **25%**.
- **Secondary Metric:** Reduce the "warm start" (dependencies present) time by at least **40%**.
- **Functional Integrity:** The orchestrator must successfully start all services, monitor them, and perform a graceful shutdown with `Ctrl+C` exactly as the original script did.
- **Log Clarity:** The logs, despite being from parallel processes, must remain clear, correctly prefixed, and easy to understand.
- **Failure Resilience:** If a critical service (backend or bot) fails its health check, the orchestrator must identify the failure, log it clearly, and shut down all other running services cleanly.

---

#### **Phase 1: Refactor Service Start-up Methods**

The primary goal of this phase is to separate the action of _starting a process_ from the action of _verifying its health_. Each `start_*` method will now be responsible only for launching its respective service and returning the necessary information for a later, separate health check.

1.  **Modify `start_dashboard_backend()`**

    - **Remove:** The existing `time.sleep(5)` and the call to `self.wait_for_service(...)`.
    - **Change Return Value:** Instead of returning a boolean (`True`/`False`), the method will return a dictionary containing all information needed for a health check later. If the process fails to start, it will return `None`.
    - **New Signature:** `def start_dashboard_backend(self) -> dict | None:`
    - **Successful Return Example:**
      ```python
      return {
          "name": "Dashboard Backend",
          "process": process,  # The subprocess object
          "health_check_url": "http://localhost:8000/health",
          "max_wait": 45
      }
      ```

2.  **Modify `start_dashboard_frontend()`**

    - **Remove:** The `time.sleep(3)` and the call to `self.wait_for_service(...)`.
    - **Change Return Value:** It will return a similar dictionary or `None`.
    - **New Signature:** `def start_dashboard_frontend(self) -> dict | None:`
    - **Successful Return Example:**
      ```python
      return {
          "name": "Dashboard Frontend",
          "process": process,
          "health_check_url": "http://localhost:5173",
          "max_wait": 15
      }
      ```

3.  **Modify `start_trading_bot()`**
    - **No Health Check:** This service doesn't have an HTTP endpoint.
    - **Change Return Value:** It will return a dictionary indicating no web health check is needed, or `None` on failure.
    - **New Signature:** `def start_trading_bot(self) -> dict | None:`
    - **Successful Return Example:**
      ```python
      return {
          "name": "Trading Bot",
          "process": process,
          "health_check_url": None  # Explicitly no health check
      }
      ```

---

#### **Phase 2: Implement Concurrent Health Check System**

This phase introduces a new component to manage health checks in parallel, leveraging Python's built-in concurrency features.

1.  **Add Imports:**

    - I will add `import concurrent.futures` at the top of the file.

2.  **Create New Method: `await_services_ready(services_to_check)`**
    - **Purpose:** This method will take a list of service dictionaries (from Phase 1) and run their health checks concurrently.
    - **Signature:** `def await_services_ready(self, services_to_check: list) -> bool:`
    - **Logic:**
      1.  Initialize a `ThreadPoolExecutor`: `with concurrent.futures.ThreadPoolExecutor() as executor:`.
      2.  Create a dictionary to map each running task (`Future`) back to the service name: `future_to_service = {}`.
      3.  Iterate through `services_to_check`. For each service that has a `health_check_url`, I will submit a task to the executor:
          ```python
          future = executor.submit(self.wait_for_service, service['name'], service['health_check_url'], service['max_wait'])
          future_to_service[future] = service['name']
          ```
      4.  Initialize a tracking variable: `all_healthy = True`.
      5.  Iterate through the completed futures as they finish: `for future in concurrent.futures.as_completed(future_to_service):`.
      6.  For each completed future, get its result. If a health check failed (result is `False`), I will log the specific failure and set `all_healthy = False`.
    - **Return Value:** The method will return `True` only if _all_ submitted health checks passed, otherwise `False`.

---

#### **Phase 3: Restructure the Main Deployment Logic**

This phase ties everything together by modifying the main `run_deployment` method to use the new parallel architecture.

1.  **Overhaul `run_deployment()`:**
    - **Initialization:**
      - Log that the parallel deployment is starting.
      - Create an empty list to hold the launched service information: `launched_services = []`.
    - **Launch Services:**
      - Call `self.start_dashboard_backend()`, `self.start_dashboard_frontend()`, and `self.start_trading_bot()` in quick succession.
      - For each call, if the returned value is not `None`, append it to the `launched_services` list.
      - **Crucial Check:** Verify that the essential services (backend and bot) were at least launched. If their process objects are missing from `launched_services`, log a critical error and trigger an immediate shutdown.
    - **Perform Concurrent Health Checks:**
      - Call the new `self.await_services_ready(launched_services)`.
      - If this method returns `False`, it signifies a health check failure. Log a critical failure message, call `shutdown_all_services()`, and terminate the deployment.
    - **Finalization:**
      - If the health checks pass, set `self.startup_complete = True`.
      - Log a clear success message: "✅ All services are up, running, and healthy."
      - Call `self.print_status_dashboard()`.
      - Proceed to the `self.monitor_processes()` loop to watch for services terminating during runtime.

---

### **Testing Strategy & Validation**

To validate the changes and ensure success criteria are met:

1.  **Benchmark the Original:** Run the current script 3 times and record the average startup time from a "warm start".
2.  **Implement Changes:** Apply the planned modifications.
3.  **Benchmark the New Version:** Run the modified script 3 times and record the average "warm start" time. Compare with the benchmark to validate the **40% improvement** goal.
4.  **Test Graceful Shutdown:** Once running, use `Ctrl+C` to ensure all subprocesses (backend, frontend, bot) are terminated correctly.
5.  **Test Failure Scenario:** Intentionally introduce an error (e.g., use a wrong port in the `start_dashboard_backend` command). The orchestrator should detect the health check failure and shut down all other services cleanly without hanging.
6.  **Test "Cold Start":** Delete the `node_modules` and `jurigged` installation. Run the script and time it. Validate the **25% improvement** goal.

### **Potential Risks & Mitigation**

- **Risk:** Logs from parallel processes become interleaved and difficult to read.
  - **Mitigation:** The existing `log` function already prefixes messages with a timestamp and service name (`[Dashboard Backend-out]`, `[Trading Bot-out]`), which should be sufficient to maintain clarity. No further action is needed unless testing proves otherwise.
- **Risk:** Increased script complexity makes future debugging more difficult.
  - **Mitigation:** I will ensure the new code is well-commented, uses clear variable names, and has strong type hinting to improve readability and maintainability.
- **Risk:** A service reports "healthy" via its HTTP endpoint before it is fully initialized, causing race conditions.
  - **Mitigation:** The health check endpoints (`/health`) are assumed to be reliable indicators of service readiness. This is a reasonable assumption for this project's architecture.

### **Rollback Plan**

- This entire plan will be executed on the `feature/validation-optimization` branch. In case of unresolvable issues or failure to meet success criteria, we can revert all changes with a single Git command:
  ```bash
  git checkout -- scripts/testnet_orchestrator_hotreload.py
  ```
