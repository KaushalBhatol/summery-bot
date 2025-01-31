// static/js/scripts.js

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const loadingIndicator = document.getElementById("loading");
    let uid = localStorage.getItem('uid');

    // Generate a unique UID if not present
    if (!uid) {
        uid = generateUUID();
        localStorage.setItem('uid', uid);
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message === "") return;

        appendMessage("user", message);
        userInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;

        // Show loading indicator
        loadingIndicator.style.display = "block";

        try {
            const response = await fetch("/get", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: message, uid: uid }),
            });

            const data = await response.json();
            // Update uid in case it was generated by the server
            if (data.uid && data.uid !== uid) {
                uid = data.uid;
                localStorage.setItem('uid', uid);
            }
            appendMessage("bot", data.response, true); // Pass true to indicate HTML content
            chatBox.scrollTop = chatBox.scrollHeight;
        } catch (error) {
            console.error("Error:", error);
            appendMessage("bot", "Sorry, something went wrong.", false);
            chatBox.scrollTop = chatBox.scrollHeight;
        } finally {
            // Hide loading indicator
            loadingIndicator.style.display = "none";
        }
    });

    function appendMessage(sender, message, isHTML = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender);

        const messageContent = document.createElement("p");
        if (isHTML) {
            messageContent.innerHTML = message;
        } else {
            messageContent.textContent = message;
        }

        messageDiv.appendChild(messageContent);
        chatBox.appendChild(messageDiv);
    }

    function generateUUID() {
        // Generate a simple UUID
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
});
