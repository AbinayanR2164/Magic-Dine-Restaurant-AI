// ======================================================
// MAGICDINE AI - FRONTEND SCRIPT
// ======================================================


// ======================================================
// CONFIGURATION
// ======================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ======================================================
// DOM ELEMENTS
// ======================================================

const input = document.querySelector(".chat-input input");
const sendButton = document.querySelector(".chat-input button");
const messages = document.querySelector(".chat-messages");


// ======================================================
// ASK AI
// ======================================================

async function askAI(question) {

    // If called from HTML without a parameter,
    // get the value from the input box.
    if (typeof question !== "string") {

        if (!input) {
            return;
        }

        question = input.value;
    }

    question = question.trim();

    if (question === "") {
        return;
    }


    // ==================================================
    // SHOW USER MESSAGE
    // ==================================================

    if (messages) {

        messages.innerHTML += `
            <div class="message user-message">
                <div class="message-content">
                    <strong>You</strong>
                    <p>${escapeHTML(question)}</p>
                </div>
            </div>
        `;

        messages.scrollTop = messages.scrollHeight;
    }


    // ==================================================
    // CLEAR INPUT
    // ==================================================

    if (input) {
        input.value = "";
    }


    // ==================================================
    // DISABLE SEND BUTTON
    // ==================================================

    if (sendButton) {
        sendButton.disabled = true;
        sendButton.style.opacity = "0.6";
        sendButton.style.cursor = "not-allowed";
    }


    // ==================================================
    // LOADING MESSAGE
    // ==================================================

    const loadingId = "ai-loading-" + Date.now();

    if (messages) {

        messages.innerHTML += `
            <div class="message ai-message" id="${loadingId}">

                <div class="message-avatar">
                    ✨
                </div>

                <div class="message-content">

                    <strong>MagicDine AI</strong>

                    <p>
                        Analyzing your restaurant data...
                    </p>

                </div>

            </div>
        `;

        messages.scrollTop = messages.scrollHeight;
    }


    try {

        // ==================================================
        // CALL FASTAPI
        // ==================================================

        const response = await fetch(
            `${API_BASE_URL}/ask?question=${encodeURIComponent(question)}`
        );


        // ==================================================
        // CHECK RESPONSE
        // ==================================================

        if (!response.ok) {

            throw new Error(
                `Backend returned ${response.status}`
            );
        }


        const data = await response.json();


        // ==================================================
        // REMOVE LOADING
        // ==================================================

        const loadingMessage =
            document.getElementById(loadingId);

        if (loadingMessage) {
            loadingMessage.remove();
        }


        // ==================================================
        // GET ANSWER
        // ==================================================

        let answer = data.answer;


        if (
            answer === null ||
            answer === undefined ||
            answer === ""
        ) {

            throw new Error(
                "No AI answer received"
            );
        }


        // ==================================================
        // SAFETY:
        // IF ANSWER IS A STRING, TRY TO PARSE JSON
        // ==================================================

        if (typeof answer === "string") {

            try {

                answer = JSON.parse(answer);

            } catch (error) {

                // If the response is normal Markdown/text,
                // convert it into our standard response format.

                answer = convertMarkdownToJSON(answer);
            }
        }


        // ==================================================
        // DISPLAY CLEAN STRUCTURED RESPONSE
        // ==================================================

        if (messages) {

            messages.innerHTML += `
                <div class="message ai-message">

                    <div class="message-avatar">
                        ✨
                    </div>

                    <div class="message-content">

                        <strong>MagicDine AI</strong>

                        ${formatAIResponse(answer)}

                    </div>

                </div>
            `;

            messages.scrollTop = messages.scrollHeight;
        }


    } catch (error) {

        console.error("AI Error:", error);


        // ==================================================
        // REMOVE LOADING
        // ==================================================

        const loadingMessage =
            document.getElementById(loadingId);

        if (loadingMessage) {
            loadingMessage.remove();
        }


        // ==================================================
        // SHOW ERROR MESSAGE
        // ==================================================

        if (messages) {

            messages.innerHTML += `
                <div class="message ai-message">

                    <div class="message-avatar">
                        ⚠️
                    </div>

                    <div class="message-content">

                        <strong>MagicDine AI</strong>

                        <p>
                            Sorry, I couldn't connect to the AI service.
                            Please make sure the MagicDine backend is running.
                        </p>

                    </div>

                </div>
            `;

            messages.scrollTop = messages.scrollHeight;
        }

    } finally {

        // ==================================================
        // RE-ENABLE SEND BUTTON
        // ==================================================

        if (sendButton) {

            sendButton.disabled = false;
            sendButton.style.opacity = "";
            sendButton.style.cursor = "";
        }
    }
}


// ======================================================
// SEND BUTTON
// ======================================================

if (sendButton) {

    sendButton.addEventListener("click", () => {

        askAI();

    });
}


// ======================================================
// ENTER KEY
// ======================================================

if (input) {

    input.addEventListener("keypress", (event) => {

        if (event.key === "Enter") {

            event.preventDefault();

            askAI();

        }

    });
}


// ======================================================
// SUGGESTION BUTTONS
// ======================================================

function attachSuggestionHandlers() {

    const suggestionButtons =
        document.querySelectorAll(".suggestions button");


    suggestionButtons.forEach(button => {

        // Prevent duplicate event listeners
        if (button.dataset.aiBound === "true") {
            return;
        }

        button.dataset.aiBound = "true";


        button.addEventListener("click", () => {

            let question = button.textContent.trim();


            // Remove common suggestion icons
            question = question
                .replace("📉", "")
                .replace("📈", "")
                .replace("🎁", "")
                .replace("👥", "")
                .replace("💰", "")
                .replace("📊", "")
                .replace("🤝", "")
                .replace("✨", "")
                .trim();


            if (question === "") {
                return;
            }


            askAI(question);

        });

    });
}


// ======================================================
// INITIAL SUGGESTION HANDLERS
// ======================================================

attachSuggestionHandlers();


// ======================================================
// FORMAT AI RESPONSE
// ======================================================

function formatAIResponse(answer) {

    let html = "";


    // ==================================================
    // SAFETY CHECK
    // ==================================================

    if (!answer) {

        return `
            <div class="ai-summary">
                <p>
                    No useful AI response was returned.
                </p>
            </div>
        `;
    }


    // ==================================================
    // SUMMARY
    // ==================================================

    if (answer.summary) {

        html += `
            <div class="ai-summary">

                <p>
                    ${escapeHTML(
                        cleanMarkdown(answer.summary)
                    )}
                </p>

            </div>
        `;
    }


    // ==================================================
    // METRICS
    // ==================================================

    if (
        Array.isArray(answer.metrics) &&
        answer.metrics.length > 0
    ) {

        html += `
            <div class="ai-section">

                <h3>
                    Quick Snapshot
                </h3>

                <div class="ai-metrics">
        `;


        answer.metrics.forEach(metric => {

            if (!metric) {
                return;
            }


            const label =
                metric.label !== undefined
                    ? metric.label
                    : "";

            const value =
                metric.value !== undefined
                    ? metric.value
                    : "";


            html += `
                <div class="ai-metric">

                    <span class="ai-metric-label">
                        ${escapeHTML(
                            cleanMarkdown(label)
                        )}
                    </span>

                    <strong class="ai-metric-value">
                        ${escapeHTML(
                            cleanMarkdown(value)
                        )}
                    </strong>

                </div>
            `;

        });


        html += `
                </div>

            </div>
        `;
    }


    // ==================================================
    // RECOMMENDATIONS
    // ==================================================

    if (
        Array.isArray(answer.recommendations) &&
        answer.recommendations.length > 0
    ) {

        html += `
            <div class="ai-section">

                <h3>
                    Recommendations
                </h3>

                <div class="ai-recommendations">
        `;


        answer.recommendations
            .slice(0, 5)
            .forEach((recommendation, index) => {

                if (!recommendation) {
                    return;
                }


                const title =
                    recommendation.title !== undefined
                        ? recommendation.title
                        : "Recommendation";


                const description =
                    recommendation.description !== undefined
                        ? recommendation.description
                        : "";


                html += `
                    <div class="ai-recommendation">

                        <div class="recommendation-number">
                            ${index + 1}
                        </div>

                        <div class="recommendation-content">

                            <strong>
                                ${escapeHTML(
                                    cleanMarkdown(title)
                                )}
                            </strong>

                            <p>
                                ${escapeHTML(
                                    cleanMarkdown(description)
                                )}
                            </p>

                        </div>

                    </div>
                `;

            });


        html += `
                </div>

            </div>
        `;
    }


    // ==================================================
    // FALLBACK
    // ==================================================

    if (html.trim() === "") {

        if (typeof answer === "string") {

            html += `
                <div class="ai-summary">

                    <p>
                        ${escapeHTML(
                            cleanMarkdown(answer)
                        )}
                    </p>

                </div>
            `;

        } else {

            html += `
                <div class="ai-summary">

                    <p>
                        MagicDine AI returned a response,
                        but it could not be displayed in
                        the expected format.
                    </p>

                </div>
            `;
        }
    }


    return html;
}


// ======================================================
// CONVERT OLD MARKDOWN RESPONSE
// ======================================================

function convertMarkdownToJSON(text) {

    if (text === null || text === undefined) {

        return {
            summary: "",
            metrics: [],
            recommendations: []
        };
    }


    // ==================================================
    // REMOVE CODE FENCES
    // ==================================================

    text = String(text)
        .replace(/```json/gi, "")
        .replace(/```/g, "")
        .trim();


    // ==================================================
    // REMOVE MARKDOWN SYMBOLS
    // ==================================================

    const cleaned = text
        .replace(/\*\*/g, "")
        .replace(/###/g, "")
        .trim();


    return {

        summary: cleaned,

        metrics: [],

        recommendations: []

    };
}


// ======================================================
// CLEAN MARKDOWN
// ======================================================

function cleanMarkdown(text) {

    if (text === null || text === undefined) {
        return "";
    }


    return String(text)

        // Bold
        .replace(/\*\*/g, "")

        // Headings
        .replace(/###/g, "")

        // Bullet points
        .replace(/^[-*]\s+/gm, "")

        // Extra whitespace
        .trim();
}


// ======================================================
// ESCAPE HTML
// ======================================================

function escapeHTML(text) {

    if (text === null || text === undefined) {
        return "";
    }


    const div =
        document.createElement("div");


    div.textContent =
        String(text);


    return div.innerHTML;
}


// ======================================================
// MAKE FUNCTIONS AVAILABLE TO ASSISTANT.HTML
// ======================================================

// assistant.html calls this after Clear Chat
// so newly-created suggestion buttons work again.

window.askAI = askAI;
window.attachSuggestionHandlers = attachSuggestionHandlers;
window.formatAIResponse = formatAIResponse;