import speech_recognition as sr
import pyttsx3
import subprocess
import time
import threading

# Initialize the recognizer for speech-to-text
recognizer = sr.Recognizer()

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1)  # Volume level

# Set up an event to control the speech loop
stop_flag = threading.Event()

# Function to speak the response
def speak(response):
    engine.say(response)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        
        # Configure recognition parameters
        recognizer.energy_threshold = 1000  # Minimum audio energy to detect
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 2.0  # Seconds of silence before considering the phrase complete
        recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speech a phrase
        
        try:
            # Listen for speech and convert to text
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=None)
            # Save the audio to a file for debugging
            with open("debug_audio.wav", "wb") as f:
                f.write(audio.get_wav_data())
                
            user_input = recognizer.recognize_google(audio)
            print(f"You said: {user_input}")
            return user_input
            
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period")
            return None
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            return "Sorry, I did not understand that."
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return f"Could not request results; {e}"

# ... existing imports and initialization code ...

def chat():
    print("👋 Hi! I'm your AI assistant. How can I help you today?")
    print("-" * 50)
    
    while not stop_flag.is_set():
        try:
            print("\n🎤 Listening...")
            time.sleep(0.5)  # Small pause before listening
            
            user_input = listen()
            if user_input:
                print(f"You: {user_input}")
                print("⌛ Processing...")
                response = process_query(user_input)
                if response:
                    print(f"\n🤖 Assistant: {response}")
                    speak(response)
                    if stop_flag.is_set():
                        break
                    print("\n" + "="* 50)
                    print("👂 What else can I help you with?")
                    time.sleep(2)  # Longer pause after speaking
        except Exception as e:
            print("I didn't catch that. Could you please try again?")
            time.sleep(1)

def process_query(query):
    if query.lower() in ["close bot", "exit", "stop", "quit"]:
        print("\nGoodbye! Have a great day!")
        stop_flag.set()
        return "Goodbye! Have a great day!"

    try:
        system_prompt = "Respond briefly in 1-2 sentences only."
        modified_query = f"{system_prompt}\nUser query: {query}"
        
        startupinfo = None
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            ["ollama", "run", "llama2", modified_query],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
            startupinfo=startupinfo
        )
        
        return result.stdout.strip() if result.returncode == 0 else "I'm not sure about that."
    except Exception as e:
        return "I'm having trouble with that request."
            
if __name__ == "__main__":
    try:
        chat_thread = threading.Thread(target=chat)
        chat_thread.start()
        while chat_thread.is_alive():
            chat_thread.join(timeout=1)
    except KeyboardInterrupt:
        stop_flag.set()
        chat_thread.join()
