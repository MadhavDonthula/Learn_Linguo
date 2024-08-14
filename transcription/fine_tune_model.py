import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import nltk
from nltk.corpus import stopwords

# Download and load NLTK stopwords
nltk.download('stopwords')

# Sample questions
questions = [
    "Bonjour, comment ça va?", "Quel âge avez-vous?", "D'où venez-vous?", 
    "Quelle est votre couleur préférée?", "Quel est votre plat préféré?", 
    "Avez-vous des frères et sœurs?", "Qu'aimez-vous faire pendant votre temps libre?", 
    "Quel est votre animal préféré?", "Quelle est la date aujourd'hui?", 
    "Comment s'appelle votre école?"
]

# Good and bad responses for each question
good_responses = {
    "Bonjour, comment ça va?": [
        "Je vais bien, merci.",
        "Ça va très bien, et vous?",
        "Je suis en pleine forme.",
        "Tout va bien, merci.",
        "Ça va, merci pour demander.",
        "Je me sens bien aujourd'hui.",
        "Je suis heureux, merci.",
        "Ça va super, et toi?",
        "Je suis en excellente forme.",
        "Je vais très bien, merci beaucoup.",
        "Je me porte bien, merci.",
        "Je suis satisfait, merci.",
        "Tout va bien, merci.",
        "Je suis en bonne santé.",
        "Je vais très bien, merci beaucoup."
    ],
    "Quel âge avez-vous?": [
        "J'ai vingt ans.",
        "Je suis âgé de vingt ans.",
        "Je viens de fêter mes vingt ans.",
        "Je suis dans ma vingtaine.",
        "Je suis âgé de 20 ans.",
        "J'ai 20 ans.",
        "J'ai eu 20 ans récemment.",
        "Je suis dans ma vingtième année.",
        "Je suis âgé de 20 années.",
        "Je viens d'avoir 20 ans.",
        "J'ai exactement vingt ans.",
        "Je suis en âge de vingt ans.",
        "Je suis âgé de vingt années.",
        "J'ai vingt ans tout juste.",
        "Je viens de célébrer mes vingt ans."
    ],
    "D'où venez-vous?": [
        "Je viens de Paris.",
        "Je suis originaire de Paris.",
        "Je viens de la capitale française.",
        "Je suis de Paris.",
        "Je suis parisien(ne).",
        "Je viens de Paris, France.",
        "Je suis de la ville lumière.",
        "Je suis originaire de Paris, France.",
        "Je viens de la région parisienne.",
        "Je suis de Paris, tout simplement.",
        "Je viens de Paris, la ville des lumières.",
        "Je suis de Paris, la capitale.",
        "Je viens de la belle ville de Paris.",
        "Je suis de Paris, capitale française.",
        "Je viens de Paris, en France."
    ],
    "Quelle est votre couleur préférée?": [
        "Ma couleur préférée est le bleu.",
        "Je préfère la couleur bleue.",
        "Le bleu est ma couleur favorite.",
        "Ma couleur favorite est le bleu.",
        "J'aime le bleu.",
        "Je trouve que le bleu est magnifique.",
        "Ma couleur préférée est le bleu clair.",
        "Je suis fan de la couleur bleue.",
        "Le bleu est ma couleur préférée.",
        "Je préfère le bleu au rouge.",
        "Je choisis le bleu comme couleur préférée.",
        "J'adore le bleu.",
        "Ma couleur préférée est le bleu foncé.",
        "Je suis attiré par le bleu.",
        "Le bleu est ma couleur préférée."
    ],
    "Quel est votre plat préféré?": [
        "Mon plat préféré est la pizza.",
        "J'adore la pizza.",
        "Je préfère manger de la pizza.",
        "La pizza est mon plat favori.",
        "Mon plat préféré est les lasagnes.",
        "Je suis fan de pizza.",
        "Je préfère les plats italiens comme la pizza.",
        "La pizza est mon plat préféré.",
        "Mon plat favori est la pizza margherita.",
        "Je choisis toujours la pizza.",
        "La pizza est mon plat préféré par excellence.",
        "Je préfère les pizzas aux autres plats.",
        "Mon plat préféré est la pizza avec des légumes.",
        "Je suis un amateur de pizza.",
        "Je préfère la pizza à tout autre plat."
    ],
    "Avez-vous des frères et sœurs?": [
        "Oui, j'ai un frère et une sœur.",
        "Je suis le grand frère/la grande sœur de deux jeunes.",
        "J'ai deux frères et une sœur.",
        "Oui, j'ai plusieurs frères et sœurs.",
        "Je suis le frère/soeur aîné(e) de ma famille.",
        "Oui, j'ai deux frères et une sœur cadette.",
        "J'ai des frères et sœurs, oui.",
        "Je suis l'aîné(e) parmi mes frères et sœurs.",
        "Oui, j'ai une sœur et un frère.",
        "J'ai des frères et sœurs, trois au total.",
        "Je suis le cadet/la cadette de ma famille.",
        "Oui, j'ai deux frères et une sœur aînée.",
        "J'ai trois frères et sœurs.",
        "Je suis le frère/la sœur de quatre personnes.",
        "Oui, j'ai un frère et deux sœurs."
    ],
    "Qu'aimez-vous faire pendant votre temps libre?": [
        "J'aime lire des livres.",
        "Je passe mon temps libre à lire.",
        "Je suis passionné(e) de lecture.",
        "J'adore lire pendant mon temps libre.",
        "Je préfère lire des romans.",
        "Je passe beaucoup de temps à lire.",
        "J'aime me détendre avec un bon livre.",
        "Lire est ma passion.",
        "Je suis un amateur de livres.",
        "Je passe mon temps libre à explorer de nouveaux livres.",
        "J'aime lire des romans pendant mes loisirs.",
        "Je me détends en lisant.",
        "J'adore lire des romans pendant mon temps libre.",
        "Lire est ce que je préfère faire.",
        "Je passe du temps à lire des livres intéressants."
    ],
    "Quel est votre animal préféré?": [
        "Mon animal préféré est le chien.",
        "Je préfère les chiens aux autres animaux.",
        "J'adore les chiens.",
        "Je suis un amoureux des chiens.",
        "Le chien est mon animal favori.",
        "Mon animal préféré est le chat.",
        "Je préfère les chats aux chiens.",
        "J'aime beaucoup les chats.",
        "Je trouve les chats fascinants.",
        "Mon animal favori est le chat.",
        "Je suis un fan des chats.",
        "J'adore les chats, c'est mon animal préféré.",
        "Le chat est mon animal préféré.",
        "Je préfère les chats aux autres animaux.",
        "Je suis passionné(e) par les chats."
    ],
    "Quelle est la date aujourd'hui?": [
        "Aujourd'hui, c'est le 13 août 2024.",
        "La date du jour est le 13 août 2024.",
        "Nous sommes le 13 août 2024.",
        "Aujourd'hui, nous sommes le 13 août.",
        "La date actuelle est le 13 août 2024.",
        "C'est le 13 août aujourd'hui.",
        "Nous sommes le 13 août de l'année 2024.",
        "Aujourd'hui, c'est le 13 août.",
        "La date d'aujourd'hui est le 13 août 2024.",
        "Aujourd'hui est le 13 août.",
        "La date d'aujourd'hui est le 13 août 2024.",
        "Nous sommes au 13 août 2024.",
        "Aujourd'hui est le 13 août de l'année 2024.",
        "La date actuelle est le 13 août.",
        "C'est le 13 août 2024 aujourd'hui."
    ],
    "Comment s'appelle votre école?": [
        "Mon école s'appelle Lycée Jean Jaurès.",
        "Je fréquente l'école Lycée Jean Jaurès.",
        "L'école que je fréquente est le Lycée Jean Jaurès.",
        "Mon établissement scolaire est le Lycée Jean Jaurès.",
        "Je suis étudiant au Lycée Jean Jaurès.",
        "Mon école est le Lycée Jean Jaurès.",
        "L'école où j'étudie est le Lycée Jean Jaurès.",
        "Je vais au Lycée Jean Jaurès.",
        "Je suis au Lycée Jean Jaurès.",
        "Mon école se nomme Lycée Jean Jaurès.",
        "Je suis inscrit au Lycée Jean Jaurès.",
        "Je fréquente le Lycée Jean Jaurès.",
        "Mon établissement est le Lycée Jean Jaurès.",
        "L'école où je vais est le Lycée Jean Jaurès.",
        "Je suis au Lycée Jean Jaurès, mon école."
    ]
}

# Bad responses for each question
bad_responses = {
    "Bonjour, comment ça va?": [
        "Je suis allé au marché.",
        "Je fais du jardinage.",
        "Je regarde un film.",
        "Je lis un livre.",
        "Je cuisine.",
        "Je vais au travail.",
        "Je fais du sport.",
        "Je vais au parc.",
        "Je fais du ménage.",
        "Je fais des courses.",
        "Je prends une douche.",
        "Je fais du yoga.",
        "Je vais au café.",
        "Je fais des devoirs.",
        "Je prépare le dîner."
    ],
    "Quel âge avez-vous?": [
        "Je vais au cinéma demain.",
        "Je suis allé à la plage.",
        "Je fais du vélo tous les jours.",
        "Je viens de lire un livre.",
        "Je suis allé à une fête.",
        "Je prépare un projet.",
        "Je fais des courses.",
        "Je vais rencontrer des amis.",
        "Je vais au restaurant.",
        "Je fais du jardinage.",
        "Je vais au musée.",
        "Je fais du bricolage.",
        "Je vais à la piscine.",
        "Je regarde un documentaire.",
        "Je fais du shopping."
    ],
    "D'où venez-vous?": [
        "J'ai un chat à la maison.",
        "Je fais du sport tous les jours.",
        "Je vais au cinéma.",
        "Je travaille sur un projet.",
        "Je cuisine souvent.",
        "Je fais du bénévolat.",
        "Je me promène dans le parc.",
        "Je regarde des séries.",
        "Je lis des livres.",
        "Je fais du jardinage.",
        "Je prépare des repas.",
        "Je fais des courses.",
        "Je vais au café.",
        "Je prends des cours de danse.",
        "Je fais du yoga."
    ],
    "Quelle est votre couleur préférée?": [
        "Je parle espagnol.",
        "Je vais à l'école tous les jours.",
        "Je fais de la peinture.",
        "Je fais des sports.",
        "Je cuisine souvent.",
        "Je fais du jardinage.",
        "Je vais au travail.",
        "Je prends des cours de musique.",
        "Je regarde des films.",
        "Je fais du shopping.",
        "Je prépare des repas.",
        "Je vais au musée.",
        "Je fais de l'exercice.",
        "Je me promène dans le parc.",
        "Je fais du bricolage."
    ],
    "Quel est votre plat préféré?": [
        "Je mange des croissants.",
        "Je vais au cinéma.",
        "Je fais des courses.",
        "Je fais du jardinage.",
        "Je vais à la plage.",
        "Je fais du sport.",
        "Je me promène en ville.",
        "Je prépare des repas.",
        "Je regarde des séries.",
        "Je vais au café.",
        "Je fais du bénévolat.",
        "Je lis des livres.",
        "Je vais au parc.",
        "Je vais au musée.",
        "Je fais du yoga."
    ],
    "Avez-vous des frères et sœurs?": [
        "Je suis allé au travail.",
        "Je fais des courses.",
        "Je regarde des films.",
        "Je cuisine.",
        "Je vais à l'école.",
        "Je fais du jardinage.",
        "Je prépare le dîner.",
        "Je fais du bricolage.",
        "Je vais à la piscine.",
        "Je fais du sport.",
        "Je lis un livre.",
        "Je fais du ménage.",
        "Je prends une douche.",
        "Je vais rencontrer des amis.",
        "Je fais des courses."
    ],
    "Qu'aimez-vous faire pendant votre temps libre?": [
        "Je fais du bénévolat.",
        "Je vais au musée.",
        "Je fais du jardinage.",
        "Je prends des cours de danse.",
        "Je regarde des séries.",
        "Je fais du shopping.",
        "Je me promène dans le parc.",
        "Je prépare des repas.",
        "Je vais au café.",
        "Je fais du yoga.",
        "Je vais au cinéma.",
        "Je fais du sport.",
        "Je vais à la plage.",
        "Je fais du bricolage.",
        "Je prends des cours de musique."
    ],
    "Quel est votre animal préféré?": [
        "Je préfère les chiens aux chats.",
        "Je suis un amateur de chevaux.",
        "Je préfère les lapins.",
        "Je suis passionné par les oiseaux.",
        "Je suis attiré par les poissons.",
        "Je préfère les hamsters.",
        "Je suis fan des tortues.",
        "Je trouve les serpents fascinants.",
        "Je préfère les iguanes.",
        "Je suis attiré par les singes.",
        "Je préfère les rats.",
        "Je suis passionné par les grenouilles.",
        "Je préfère les hérissons.",
        "Je suis fasciné par les dauphins.",
        "Je préfère les ours."
    ],
    "Quelle est la date aujourd'hui?": [
        "Je suis allé à un concert hier.",
        "Je fais du jardinage.",
        "Je vais au travail.",
        "Je fais des courses.",
        "Je vais au cinéma.",
        "Je prépare des repas.",
        "Je lis un livre.",
        "Je fais du sport.",
        "Je vais au musée.",
        "Je vais à la plage.",
        "Je fais du yoga.",
        "Je fais du bricolage.",
        "Je vais rencontrer des amis.",
        "Je regarde un documentaire.",
        "Je fais du bénévolat."
    ],
    "Comment s'appelle votre école?": [
        "Je vais au Lycée Charles de Gaulle.",
        "Mon école s'appelle Collège Saint-Exupéry.",
        "Je fréquente le Lycée Albert Camus.",
        "Je suis inscrit au Collège Victor Hugo.",
        "Mon établissement est le Lycée Émile Zola.",
        "Je vais au Lycée Jean Monnet.",
        "Je fréquente le Lycée Jean-Paul Sartre.",
        "Mon école est le Collège Jules Verne.",
        "Je suis au Lycée Simone de Beauvoir.",
        "Je fréquente le Collège Pierre Corneille.",
        "Mon établissement est le Lycée André Gide.",
        "Je vais au Collège Georges Sand.",
        "Je fréquente le Lycée Marguerite Duras.",
        "Mon école est le Lycée Louis Pasteur.",
        "Je suis au Collège Claude Monet."
    ]
}

# Create a dataset where the correct answers are labeled as '1' and incorrect as '0'
data = []
for question in questions:
    if question in good_responses:
        for response in good_responses[question]:
            data.append((question + " " + response, 1))
    if question in bad_responses:
        for response in bad_responses[question]:
            data.append((question + " " + response, 0))

# Separate features and labels
texts, labels = zip(*data)

# Create a pipeline that combines a CountVectorizer with a Naive Bayes classifier
vectorizer = CountVectorizer(stop_words=stopwords.words('french'))
model = make_pipeline(vectorizer, MultinomialNB())

# Train the model
model.fit(texts, labels)

# Save the model to a file
with open('bow_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved.")
