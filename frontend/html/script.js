<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sonotheia Audio Verification Demo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>SONOTHEIA</h1>
            <p class="subtitle">Audio Authenticity Verification</p>
        </header>

        <main>
            <div class="upload-area" id="uploadArea">
                <p>Upload an audio file (.wav, .mp3) for forensic analysis.</p>
                <input type="file" id="audioFile" accept="audio/*" hidden/>
                <button id="uploadButton">Select File</button>
            </div>

            <div class="results-area" id="resultsArea" style="display: none;">
                <h2>Analysis Report</h2>
                <div id="spinner" class="spinner" style="display: none;"></div>
                <div id="resultsContent"></div>
                <button id="resetButton">Analyze Another File</button>
            </div>
        </main>
        
        <footer>
            <p>CLASSIFICATION: PROPRIETARY / CONFIDENTIAL</p>
        </footer>
    </div>
    
    <script>
    // --- EMBEDDED JAVASCRIPT ---
    document.addEventListener('DOMContentLoaded', function() {
        const uploadArea = document.getElementById('uploadArea');
        const resultsArea = document.getElementById('resultsArea');
        const uploadButton = document.getElementById('uploadButton');
        const audioFile = document.getElementById('audioFile');
        const resultsContent = document.getElementById('resultsContent');
        const spinner = document.getElementById('spinner');
        const resetButton = document.getElementById('resetButton');

        // Attach event listeners
        uploadButton.addEventListener('click', () => audioFile.click());
        audioFile.addEventListener('change', handleFileUpload);
        resetButton.addEventListener('click', resetView);

        // This function is called when a file is selected
        function handleFileUpload() {
            const file = audioFile.files[0];
            if (!file) return;

            // Switch to the results view
            uploadArea.style.display = 'none';
            resultsArea.style.display = 'block';
            spinner.style.display = 'block';
            resultsContent.innerHTML = '';

            const formData = new FormData();
            formData.append('file', file);

            // Make the API call to the backend
            fetch('/api/v2/detect/quick', {
                method: 'POST',
                body: formData,
            })
            .then(async response => {
                const isJson = response.headers.get('content-type')?.includes('application/json');
                const data = isJson ? await response.json() : await response.text();
                if (!response.ok) {
                    const errorDetail = (isJson && data.detail) ? data.detail : data;
                    throw new Error(errorDetail);
                }
                return data;
            })
            .then(data => {
                spinner.style.display = 'none';
                displayResults(data);
            })
            .catch(error => {
                spinner.style.display = 'none';
                resultsContent.innerHTML = `<p style="color: #FF3B30;"><b>API Error:</b></p><pre style="text-align: left; background-color: #333; padding: 10px; border-radius: 4px; white-space: pre-wrap;">${error.message}</pre>`;
            });
        }

        // This function renders the results from the API
        function displayResults(data) {
            const { verdict, detail, evidence } = data;
            const breath = evidence.check_breath_sensor;
            const dynamic_range = evidence.check_dynamic_range_sensor;
            const bandwidth = evidence.check_bandwidth_sensor;

            const phonationClass = breath.passed ? 'pass' : 'fail';
            const dynamicRangeClass = dynamic_range.passed ? 'pass' : 'fail';
            const bandwidthClass = bandwidth.type === 'NARROWBAND' ? 'fail' : 'pass';

            // Redacted display values - show pass/fail status without specific metrics
            const breathDisplay = breath.passed ? 'Natural breathing patterns' : 'Anomalous phonation detected';
            const dynamicRangeDisplay = dynamic_range.passed ? 'Natural dynamics detected' : 'Compressed dynamics detected';
            const bandwidthDisplay = bandwidth.type === 'NARROWBAND' ? 'Limited frequency range detected' : 
                                     bandwidth.type === 'FULLBAND' ? 'Full frequency range' :
                                     bandwidth.type === 'SILENCE' ? 'No audio detected' : 'Analysis complete';

            resultsContent.innerHTML = `
                <div class="verdict-section">
                    <div class="verdict verdict-${verdict}">${verdict}</div>
                    <p>${detail}</p>
                </div>

                <table class="evidence-table">
                    <thead>
                        <tr>
                            <th colspan="2">Forensic Evidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="label">Breath Pattern Analysis</td>
                            <td class="value ${phonationClass}">${breathDisplay}</td>
                        </tr>
                        <tr>
                            <td class="label">Dynamic Range Analysis</td>
                            <td class="value ${dynamicRangeClass}">${dynamicRangeDisplay}</td>
                        </tr>
                        <tr>
                            <td class="label">Bandwidth Analysis</td>
                            <td class="value ${bandwidthClass}">${bandwidthDisplay}</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
        
        // This function resets the UI to the initial state
        function resetView() {
            uploadArea.style.display = 'block';
            resultsArea.style.display = 'none';
            audioFile.value = ''; // Reset file input
        }
    });
    </script>
</body>
</html>
