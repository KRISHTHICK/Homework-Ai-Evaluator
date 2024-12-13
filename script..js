const form = document.getElementById('upload-form');
const resultDiv = document.getElementById('result');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = document.getElementById('homework-file').files[0];

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8080/evaluate_homework', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (data.error) {
      resultDiv.textContent = data.error;
    } else {
      // Parse the JSON response
      const evaluation = JSON.parse(data);

      // Format the output as text
      let text = "Response -- \n";
      text += `Accuracy Score: ${evaluation.response.accuracy_score}\n`;
      text += `Grammar Score: ${evaluation.response.grammar_score}\n`;
      text += `Writing style Score: ${evaluation.response.writing_style_score}`;

      resultDiv.textContent = text;
    }
  } catch (error) {
    console.error(error);
    resultDiv.textContent = 'Error evaluating homework.';
  }
});
