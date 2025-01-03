import speech_recognition as sr
import pyttsx3
import subprocess
import time
import threading
from colorama import init, Fore, Style
import json
import random
from datetime import datetime

# Initialize colorama
init()

# Initialize the recognizer for speech-to-text
recognizer = sr.Recognizer()

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1)  # Volume level

# Configuration
CONFIG = {
    "wake_word": "hey assistant",
    "voice_rate": 150,
    "voice_volume": 1.0,
    "energy_threshold": 1000,
    "timeout": 10,
    "voices": {},  # Will be populated after init
}

# Initialize voice options
voices = engine.getProperty('voices')
CONFIG["voices"] = {voice.name: voice.id for voice in voices}
engine.setProperty('voice', voices[0].id)  # Default voice

def change_voice(voice_index):
    if 0 <= voice_index < len(voices):
        engine.setProperty('voice', voices[voice_index].id)
        speak("Voice changed successfully")

def save_conversation(user_input, response):
    with open("conversation_history.txt", "a", encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}]\nUser: {user_input}\nAssistant: {response}\n{'-'*50}")

def process_commands(query):
    commands = {
        "change voice": lambda: change_voice(random.randint(0, len(voices)-1)),
        "speak faster": lambda: engine.setProperty('rate', min(CONFIG["voice_rate"] + 50, 300)),
        "speak slower": lambda: engine.setProperty('rate', max(CONFIG["voice_rate"] - 50, 100)),
        "volume up": lambda: engine.setProperty('volume', min(CONFIG["voice_volume"] + 0.1, 1.0)),
        "volume down": lambda: engine.setProperty('volume', max(CONFIG["voice_volume"] - 0.1, 0.1))
    }
    
    for cmd, func in commands.items():
        if cmd in query.lower():
            func()
            return True
    return False

# Set up an event to control the speech loop
stop_flag = threading.Event()

# Function to speak the response
def speak(response):
    engine.say(response)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print(f"{Fore.YELLOW}Adjusting for ambient noise...{Style.RESET_ALL}")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Visual feedback
        print(f"{Fore.GREEN}🎤 Listening...{Style.RESET_ALL}")
        
        try:
            audio = recognizer.listen(source, timeout=CONFIG["timeout"])
            user_input = recognizer.recognize_google(audio)
            print(f"{Fore.CYAN}You said: {user_input}{Style.RESET_ALL}")
            return user_input.lower()
        except sr.WaitTimeoutError:
            print(f"{Fore.RED}⏰ Listening timeout{Style.RESET_ALL}")
        except sr.UnknownValueError:
            print(f"{Fore.RED}🤔 Could not understand audio{Style.RESET_ALL}")
        except sr.RequestError as e:
            print(f"{Fore.RED}🌐 API Error: {e}{Style.RESET_ALL}")
        return None

def chat():
    print(f"{Fore.GREEN}{'='*50}")
    print("🤖 AI Assistant v2.0")
    print(f"💡 Say '{CONFIG['wake_word']}' to get my attention!")
    print(f"{'='*50}{Style.RESET_ALL}")
    
    waiting_for_wake_word = True
    
    while not stop_flag.is_set():
        try:
            if waiting_for_wake_word:
                user_input = listen()
                if user_input and CONFIG["wake_word"] in user_input:
                    waiting_for_wake_word = False
                    speak("Hello! How can I help you?")
                continue
            
            user_input = listen()
            if not user_input:
                continue
                
            # Check for commands first
            if process_commands(user_input):
                continue
                
            # Process normal queries
            print(f"{Fore.YELLOW}⌛ Processing...{Style.RESET_ALL}")
            response = process_query(user_input)
            
            if response:
                print(f"\n{Fore.GREEN}🤖 Assistant: {response}{Style.RESET_ALL}")
                speak(response)
                save_conversation(user_input, response)
                
                if stop_flag.is_set():
                    break
                    
                print(f"\n{Fore.CYAN}{'='*50}")
                print("👂 What else can I help you with?")
                print(f"{'='*50}{Style.RESET_ALL}")
                time.sleep(1)
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
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

def cleanup():
    print(f"{Fore.YELLOW}Cleaning up...{Style.RESET_ALL}")
    stop_flag.set()
    engine.stop()
            
if __name__ == "__main__":
    try:
        chat_thread = threading.Thread(target=chat)
        chat_thread.start()
        
        while chat_thread.is_alive():
            chat_thread.join(timeout=1)
    except KeyboardInterrupt:
        cleanup()
    finally:
        print(f"{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
