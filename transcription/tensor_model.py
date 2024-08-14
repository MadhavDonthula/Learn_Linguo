import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, LSTM, Dropout
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Sample data
questions = [
    "Bonjour, comment ça va?", "Quel âge avez-vous?", "D'où venez-vous?", 
    "Quelle est votre couleur préférée?"
]

good_responses = {
    "Bonjour, comment ça va?": [
        "Je suis en pleine forme.", "Tout va bien, merci pour demander.", "Je suis très heureux aujourd'hui.",
        "Je me sens excellent.", "Je suis en bonne santé, merci.", "Je me porte bien aujourd'hui.",
        "Je suis dans une bonne humeur.", "Ça va très bien, je vous remercie.", "Je suis en parfaite forme.",
        "Je vais super bien, merci.", "Je suis en excellente santé.", "Tout est parfait, merci.",
        "Je suis en grande forme.", "Je me sens très bien aujourd'hui.", "Je vais très bien, merci beaucoup."
    ],
    "Quel âge avez-vous?": [
        "Je suis âgé de vingt ans.", "J'ai récemment fêté mes vingt ans.", "Je viens d'avoir vingt ans.",
        "Je suis âgé de 20 années.", "Je viens juste d'avoir vingt ans.", "J'ai atteint l'âge de vingt ans récemment.",
        "Je viens de célébrer mes vingt ans.", "Je suis dans ma vingtième année.", "Je suis âgé de 20 ans tout juste.",
        "J'ai eu vingt ans il y a peu.", "Je suis dans ma vingtaine.", "Je viens d'avoir 20 ans.",
        "Je suis en âge de vingt ans.", "Je viens de marquer mes vingt ans.", "Je suis âgé de vingt ans maintenant."
    ],
    "D'où venez-vous?": [
        "Je viens de Lyon.", "Je suis originaire de Lyon.", "Je viens de la région lyonnaise.",
        "Je suis de Lyon, en France.", "Je viens de la ville de Lyon.", "Je suis de la région de Lyon.",
        "Je viens de Lyon, la grande ville.", "Je suis de Lyon, capitale des Gaules.", "Je viens de la ville de Lyon.",
        "Je suis originaire de Lyon, France.", "Je viens de Lyon, au centre-est de la France.", "Je suis de Lyon, une ville historique.",
        "Je viens de la belle ville de Lyon.", "Je suis de Lyon, au sud-est de la France.", "Je viens de la capitale des Gaules, Lyon."
    ],
    "Quelle est votre couleur préférée?": [
        "J'adore le vert.", "Ma couleur préférée est le rouge.", "Je préfère le vert émeraude.",
        "Le rouge est ma couleur favorite.", "Je trouve le vert très apaisant.", "Le rouge est la couleur que je préfère.",
        "Je préfère le vert intense.", "Je suis fan de la couleur verte.", "Je choisis le rouge comme couleur préférée.",
        "Je suis attiré par le vert.", "Ma couleur préférée est le bleu clair.", "Je préfère le bleu au rouge.",
        "Je trouve que le bleu est magnifique.", "J'adore le rouge.", "Je suis passionné par le bleu."
    ]
}

bad_responses = {
    "Bonjour, comment ça va?": [
        "Je suis allé au marché.", "Je fais du jardinage.", "Je regarde un film.", "Je lis un livre.",
        "Je cuisine.", "Je vais au travail.", "Je fais du sport.", "Je vais au parc.", "Je fais du ménage.",
        "Je fais des courses.", "Je prends une douche.", "Je fais du yoga.", "Je vais au café.", "Je fais des devoirs.",
        "Je prépare le dîner."
    ],
    "Quel âge avez-vous?": [
        "Je vais au cinéma demain.", "Je suis allé à la plage.", "Je fais du vélo tous les jours.",
        "Je viens de lire un livre.", "Je suis allé à une fête.", "Je prépare un projet.", "Je fais des courses.",
        "Je vais rencontrer des amis.", "Je vais au restaurant.", "Je fais du jardinage.", "Je vais au musée.",
        "Je fais du bricolage.", "Je vais à la piscine.", "Je regarde un documentaire.", "Je fais du shopping."
    ],
    "D'où venez-vous?": [
        "J'ai un chat à la maison.", "Je fais du sport tous les jours.", "Je vais au cinéma.", "Je travaille sur un projet.",
        "Je cuisine souvent.", "Je fais du bénévolat.", "Je me promène dans le parc.", "Je regarde des séries.",
        "Je lis des livres.", "Je fais du jardinage.", "Je prépare des repas.", "Je fais des courses.", "Je vais au café.",
        "Je prends des cours de danse.", "Je fais du yoga."
    ],
    "Quelle est votre couleur préférée?": [
        "Je parle espagnol.", "Je vais à l'école tous les jours.", "Je fais de la peinture.", "Je fais des sports.",
        "Je cuisine souvent.", "Je fais du jardinage.", "Je vais au travail.", "Je prends des cours de musique.",
        "Je regarde des films.", "Je fais du shopping.", "Je prépare des repas.", "Je vais au musée.",
        "Je fais de l'exercice.", "Je me promène dans le parc.", "Je fais du bricolage."
    ]
}

# Prepare data
texts = []
labels = []
label_map = {}

for i, question in enumerate(questions):
    # Add good responses
    for response in good_responses.get(question, []):
        texts.append(f"{question} {response}")
        labels.append(f"good_{i}")
    
    # Add bad responses
    for response in bad_responses.get(question, []):
        texts.append(f"{question} {response}")
        labels.append(f"bad_{i}")

# Convert labels to integers
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)

# Tokenize text data
tokenizer = Tokenizer()
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
X = pad_sequences(sequences)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)

# Build the model
model = Sequential()
model.add(Embedding(input_dim=len(tokenizer.word_index) + 1, output_dim=128, input_length=X.shape[1]))
model.add(LSTM(64, return_sequences=True))
model.add(Dropout(0.5))
model.add(LSTM(64))
model.add(Dense(len(label_encoder.classes_), activation='softmax'))

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Train the model
history = model.fit(X_train, y_train, epochs=10, validation_split=0.1, batch_size=32)

# Evaluate the model
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Loss: {loss}")
print(f"Test Accuracy: {accuracy}")

# Example prediction
def predict_response(text):
    sequence = tokenizer.texts_to_sequences([text])
    padded_sequence = pad_sequences(sequence, maxlen=X.shape[1])
    prediction = model.predict(padded_sequence)
    predicted_class = np.argmax(prediction)
    return label_encoder.inverse_transform([predicted_class])[0]

# Test predictions
sample_text = "Bonjour, comment ça va? Je me sens très bien aujourd'hui."
print("Prediction:", predict_response(sample_text))
model.save('transcription/my_model.h5')
