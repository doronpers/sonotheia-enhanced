"""
Streamlit UI for Sonotheia MVP

Simple web interface for audio upload, analysis, and visualization.
"""

import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure page
st.set_page_config(
    page_title="Sonotheia MVP - Voice Deepfake Detection",
    page_icon="🎙️",
    layout="wide"
)

# API endpoint
API_BASE_URL = "http://localhost:8000"


def plot_waveform(viz_data):
    """Plot waveform comparison"""
    waveform = viz_data['waveform']

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Original Audio', 'Codec-Processed Audio'),
        vertical_spacing=0.1
    )

    # Original waveform
    fig.add_trace(
        go.Scatter(
            x=waveform['time'],
            y=waveform['amplitude_original'],
            mode='lines',
            name='Original',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )

    # Coded waveform
    fig.add_trace(
        go.Scatter(
            x=waveform['time'],
            y=waveform['amplitude_coded'],
            mode='lines',
            name='Codec-Processed',
            line=dict(color='red', width=1)
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_yaxes(title_text="Amplitude", row=2, col=1)

    fig.update_layout(
        height=500,
        showlegend=False,
        title_text="Waveform Comparison"
    )

    return fig


def plot_spectrogram(viz_data):
    """Plot spectrogram"""
    spec_data = viz_data['spectrogram']

    # Use coded spectrogram for display
    spec = np.array(spec_data['coded'])
    freqs = np.array(spec_data['frequencies'])

    fig = go.Figure(data=go.Heatmap(
        z=spec,
        y=freqs,
        colorscale='Viridis',
        colorbar=dict(title="dB")
    ))

    fig.update_layout(
        title="Spectrogram (Codec-Processed)",
        xaxis_title="Time Frame",
        yaxis_title="Frequency (Hz)",
        height=400
    )

    return fig


def plot_risk_factors(risk_result):
    """Plot risk factors as horizontal bars"""
    factors = risk_result['factors']

    names = [f['name'].replace('_', ' ').title() for f in factors]
    scores = [f['score'] * 100 for f in factors]  # Convert to percentage
    colors = ['red' if s > 50 else 'orange' if s > 30 else 'green' for s in scores]

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation='h',
        marker=dict(color=colors),
        text=[f"{s:.1f}%" for s in scores],
        textposition='auto'
    ))

    fig.update_layout(
        title="Risk Factor Breakdown",
        xaxis_title="Risk Score (%)",
        yaxis_title="Factor",
        height=300,
        xaxis=dict(range=[0, 100])
    )

    return fig


def main():
    """Main Streamlit app"""

    st.title("🎙️ Sonotheia MVP - Voice Deepfake Detection")
    st.markdown("""
    Upload an audio file to analyze for voice deepfakes using physics-based detection.
    The system applies telephony codec simulation and extracts acoustic features to detect synthetic voice.
    """)

    # Sidebar for parameters
    st.sidebar.header("Analysis Parameters")

    codec = st.sidebar.selectbox(
        "Telephony Codec",
        options=['landline', 'mobile', 'voip', 'clean'],
        index=0,
        help="Codec simulation to apply"
    )

    channel = st.sidebar.selectbox(
        "Call Channel",
        options=['phone', 'voip', 'mobile'],
        index=0
    )

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("1. Upload Audio")

        # File upload
        audio_file = st.file_uploader(
            "Upload WAV file",
            type=['wav'],
            help="Upload a WAV audio file for analysis"
        )

        # Metadata inputs
        call_id = st.text_input("Call ID", value="CALL-001", help="Unique call identifier")
        customer_id = st.text_input("Customer ID", value="CUST-12345", help="Customer identifier")
        transaction_id = st.text_input("Transaction ID (optional)", value="TXN-001")
        amount_usd = st.number_input("Amount USD (optional)", min_value=0.0, value=50000.0, step=1000.0)
        destination_country = st.text_input("Destination Country (optional)", value="US")

        # Analyze button
        analyze_button = st.button("🔍 Analyze Call", type="primary", use_container_width=True)

    with col2:
        st.header("2. Analysis Results")

        if analyze_button:
            if not audio_file:
                st.error("Please upload an audio file first!")
            else:
                with st.spinner("Analyzing audio..."):
                    try:
                        # Prepare form data
                        files = {
                            'audio_file': (audio_file.name, audio_file.getvalue(), 'audio/wav')
                        }

                        data = {
                            'call_id': call_id,
                            'customer_id': customer_id,
                            'transaction_id': transaction_id,
                            'amount_usd': amount_usd,
                            'destination_country': destination_country,
                            'channel': channel,
                            'codec': codec
                        }

                        # Call API
                        response = requests.post(
                            f"{API_BASE_URL}/api/analyze_call",
                            files=files,
                            data=data
                        )

                        if response.status_code == 200:
                            result = response.json()

                            # Display results
                            risk_result = result['risk_result']
                            overall_score = risk_result['overall_score']
                            risk_level = risk_result['risk_level']
                            decision = risk_result['decision']

                            # Risk score display
                            st.subheader("Overall Risk Assessment")

                            # Color code based on risk level
                            risk_color = {
                                'LOW': 'green',
                                'MEDIUM': 'orange',
                                'HIGH': 'red',
                                'CRITICAL': 'darkred'
                            }.get(risk_level, 'gray')

                            st.markdown(f"""
                            <div style="padding: 20px; background-color: {risk_color}; color: white; border-radius: 10px; text-align: center;">
                                <h2>Risk Level: {risk_level}</h2>
                                <h3>Score: {overall_score*100:.1f}%</h3>
                                <h4>Decision: {decision}</h4>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("---")

                            # Display factors
                            st.subheader("Risk Factors")
                            for factor in risk_result['factors']:
                                with st.expander(f"{factor['name'].replace('_', ' ').title()} - {factor['score']*100:.1f}%"):
                                    st.write(f"**Explanation:** {factor['explanation']}")
                                    st.write(f"**Weight:** {factor['weight']}")
                                    st.write(f"**Confidence:** {factor['confidence']*100:.0f}%")

                        else:
                            st.error(f"API Error: {response.status_code}")
                            st.json(response.json())

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Visualization section (full width)
    if analyze_button and audio_file:
        if response.status_code == 200:
            st.markdown("---")
            st.header("3. Visualizations")

            viz_data = result['visualization_data']

            # Tabs for different visualizations
            tab1, tab2, tab3 = st.tabs(["Waveform", "Spectrogram", "Risk Breakdown"])

            with tab1:
                st.plotly_chart(plot_waveform(viz_data), use_container_width=True)

            with tab2:
                st.plotly_chart(plot_spectrogram(viz_data), use_container_width=True)

            with tab3:
                st.plotly_chart(plot_risk_factors(risk_result), use_container_width=True)

            # SAR narrative
            if result.get('sar_narrative'):
                st.markdown("---")
                st.header("4. SAR Narrative")
                st.text_area("Generated SAR", result['sar_narrative'], height=400)

            # Audio metadata
            st.markdown("---")
            st.header("5. Audio Metadata")
            audio_meta = result['audio_metadata']
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Duration", f"{audio_meta['duration_seconds']:.2f}s")
            with col2:
                st.metric("Sample Rate", f"{audio_meta['sample_rate']} Hz")
            with col3:
                st.metric("Codec Applied", audio_meta['codec_applied'])
            with col4:
                st.metric("Frames", audio_meta['num_frames'])

    # Footer
    st.markdown("---")
    st.markdown("""
    **Sonotheia MVP** - Physics-Based Voice Deepfake Detection

    This system uses telephony-aware codec simulation and acoustic feature analysis
    to detect synthetic and manipulated voice audio.
    """)


if __name__ == "__main__":
    main()
