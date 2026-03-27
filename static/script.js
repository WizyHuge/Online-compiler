const editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
  mode: "python",
  theme: "dracula",
  lineNumbers: true,
  indentUnit: 4,
  tabSize: 4,
  indentWithTabs: false,
  autoCloseBrackets: true,
  lineWrapping: true,
});

const runBtn = document.getElementById("run-btn");
const output = document.getElementById("output");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

function setStatus(state) {
  statusDot.className = "status-dot " + state;
  const labels = {
    idle: "Ожидание",
    running: "Выполняется...",
    done: "Готово",
    error: "Ошибка",
  };
  statusText.textContent = labels[state] || "";
}

runBtn.addEventListener("click", async () => {
  const code = editor.getValue();
  if (!code.trim()) return;

  output.textContent = "";
  runBtn.disabled = true;
  setStatus("running");

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });

    const data = await res.json();

    if (!res.ok) {
      output.textContent = data.error || "Ошибка сервера";
      setStatus("error");
      return;
    }

    const taskId = data.task_id;

    const source = new EventSource(`/api/stream/${taskId}`);

    source.onmessage = (event) => {
      const result = JSON.parse(event.data);
      source.close();

      if (result.error) {
        output.textContent = result.error;
        setStatus("error");
      } else {
        output.textContent = result.stdout || "(нет вывода)";
        if (result.stderr) {
          output.textContent += "\n\nSTDERR:\n" + result.stderr;
        }
        setStatus("done");
      }
    };

    source.onerror = () => {
      source.close();
      output.textContent = "Ошибка соединения";
      setStatus("error");
    };
  } catch (err) {
    output.textContent = "Ошибка: " + err.message;
    setStatus("error");
  } finally {
    runBtn.disabled = false;
  }
});
