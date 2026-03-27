async function runCode() {
    const code = document.getElementById("code").value;
    const output = document.getElementById("output");
    const btn = document.getElementById("run-btn");

    if (!code.trim()) {
        setOutput("Введите код для выполнения", "error");
        return;
    }

    btn.disabled = true;
    setOutput("Выполняется...", "loading");

    try {
        const response = await fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code })
        });

        const data = await response.json();

        if (data.error) {
            setOutput(`${data.error}`, "error");
        } else if (data.stderr) {
            setOutput(data.stderr, "error");
        } else {
            setOutput(data.stdout || "(нет вывода)", "success");
        }

    } catch (err) {
        setOutput(`Ошибка соединения: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
    }
}

function clearAll() {
    document.getElementById("code").value = "";
    setOutput("Результат появится здесь...", "");
}

function setOutput(text, status) {
    const output = document.getElementById("output");
    output.textContent = text;
    output.className = status;
}

document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") runCode();
});
