# Development notes

- Use a task branch and pull request for changes. Do not push directly to the default branch.
- The sensor is an MLX90641 attached through a Melexis EVB90640/41 USB board. Keep the public example service generic; deployment IPs, usernames, and local paths belong in the machine's systemd unit, not in Git.
- Run `python3 -m py_compile thermal_web.py` and `node --check static/app.js` before committing. Hardware changes also require checking `/api/frame` against the attached sensor.
- Keep the dashboard usable on desktop and mobile, and keep LAN access restricted with the host firewall.
