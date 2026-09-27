// ==========================================
// ASK INSIGHTIQ
// ==========================================

const askForm = document.getElementById("askForm");

const questionInput =
    document.getElementById("questionInput");

const answerBox =
    document.getElementById("answerBox");

const answerText =
    document.getElementById("answerText");


// ------------------------------------------
// Ask question
// ------------------------------------------

if (askForm) {

    askForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const question =
                questionInput.value.trim();

            if (!question) {

                answerBox.style.display = "block";

                answerText.textContent =
                    "Please enter a question first.";

                return;
            }


            answerBox.style.display = "block";

            answerText.textContent =
                "InsightIQ is analyzing your dataset...";


            try {

                const formData =
                    new FormData();

                formData.append(
                    "question",
                    question
                );


                const response =
                    await fetch(
                        "/ask",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                answerText.textContent =
                    data.answer;


            } catch (error) {

                answerText.textContent =
                    "Something went wrong while analyzing your question.";

                console.error(error);

            }

        }
    );

}


// ------------------------------------------
// Example questions
// ------------------------------------------

const exampleQuestions =
    document.querySelectorAll(
        ".example-question"
    );


exampleQuestions.forEach(
    function(button) {

        button.addEventListener(
            "click",
            function() {

                questionInput.value =
                    button.dataset.question;

                questionInput.focus();

            }
        );

    }
);