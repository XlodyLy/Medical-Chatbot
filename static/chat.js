function appendMessage(message, sender) {
  const chatBox = document.getElementById("chat-box");

  // Convert markdown-style formatting to HTML
  const formatted = message
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")  // Bold
    .replace(/\n/g, "<br>");                           // Line breaks

  if (sender === "bot") {
    const container = document.createElement("div");
    container.className = "bot-message-container";

    const emoji = document.createElement("div");
    emoji.className = "emoji-avatar";
    emoji.textContent = "👩‍⚕️"; // You can change to 🤖 or anything else

    const bubble = document.createElement("div");
    bubble.className = "bot-message";
    bubble.innerHTML = formatted;

    container.appendChild(emoji);
    container.appendChild(bubble);
    chatBox.appendChild(container);
  } else {
    const messageElement = document.createElement("div");
    messageElement.className = "user-message";
    messageElement.innerHTML = formatted;
    chatBox.appendChild(messageElement);
  }

  // Auto-scroll to bottom
  chatBox.scrollTop = chatBox.scrollHeight;
}


function formatBotResponse(text) {
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  const lines = text.split('\n');
  let formatted = '';
  let inBulletList = false;
  let inNumberList = false;

  lines.forEach(line => {
    const trimmed = line.trim();

    if (/^-\s+/.test(trimmed)) {
      if (!inBulletList) {
        formatted += '<ul>';
        inBulletList = true;
      }
      formatted += `<li>${trimmed.substring(2)}</li>`;
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (!inNumberList) {
        formatted += '<ol>';
        inNumberList = true;
      }
      formatted += `<li>${trimmed.replace(/^\d+\.\s+/, '')}</li>`;
    } else {
      if (inBulletList) {
        formatted += '</ul>';
        inBulletList = false;
      }
      if (inNumberList) {
        formatted += '</ol>';
        inNumberList = false;
      }
      formatted += `<p>${trimmed}</p>`;
    }
  });

  if (inBulletList) formatted += '</ul>';
  if (inNumberList) formatted += '</ol>';

  return formatted;
}



function sendMessage() {
  const userInput = document.getElementById("user-input");
  const message = userInput.value.trim();
  if (message === "") return;

  // Display user's message
  appendMessage(message, "user");

  // Clear input field
  userInput.value = "";

  // Send message to Flask backend
  fetch("/get", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ msg: message }),
  })
    .then((response) => response.json())
    .then((data) => {
      const formatted = formatBotResponse(data.response);
      appendMessage(formatted, "bot");
    })    
    .catch((error) => {
      console.error("Error:", error);
      appendMessage("Sorry, something went wrong. Please try again later.", "bot");
    });
}

window.addEventListener("DOMContentLoaded", () => {
  const welcomeText = `Hi, I am MedBot 👩‍⚕️ — your medical assistant. How can I help you today?`;
  const formatted = formatBotResponse(welcomeText);
  appendMessage(formatted, "bot");
});

// Add event listener for 'Enter' key press to send the message
document.getElementById("user-input").addEventListener("keydown", function(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();  // Prevents the default "Enter" behavior (e.g., form submission)
    sendMessage();          // Calls the function to send the message
  }
});

function scrollToBottom() {
  const chatBox = document.querySelector('.chat-box');
  chatBox.scrollTop = chatBox.scrollHeight;
}




