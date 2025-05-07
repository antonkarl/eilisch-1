from dotenv import load_dotenv
import openai
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT_1 = """Fyrir neðan er alþingisræða á íslensku. Ég vil að þú segir mér, á skala frá 0 upp í 1, hve formleg ræðan er
Ég vil ekki að þú svarir með neinu öðru en tölunni"""

PROMPT_2 = """Fyrir neðan er alþingisræða á íslensku. Ég vil að þú metir hversu formleg ræðan er á skala frá 0 upp í 1, þar sem 0 er mjög óformlegt (t.d. talmál, slangur, persónulegur tón) og 1 er mjög formlegt (t.d. notkun formlegra orða, málvenjur og alvarlegur tón). Formlega málið vísar til notkunar á formlegum orðum, málfar, og setningabyggingu. Vinsamlegast svaraðu aðeins með tölu, án þess að bæta við öðrum útskýringum."""

PROMPT_3 = """Below is a speech from the Icelandic Parliament. It is in Icelandic. I would like you to assess how formal the speech is on a scale from 0 to 1, where 0 is very informal (e.g., conversational language, slang, personal tone) and 1 is very formal (e.g., use of formal words, formal language conventions, and a serious tone). Formality refers to the use of formal words, language style, and sentence structure. Please respond only with a number, without adding any additional explanations."""


def get_response(message):
    completion = openai.Completion.create(
        model='gpt-4',
        prompt=f"{PROMPT_3}\n\n{message}",
        max_tokens=5,
        temperature=0,
        n=1
    )
    content = completion.choices[0].text.strip()
    return content

def get_scores(user_inputs):
    respones = []
    for user_input in user_inputs:
        respone = get_response(user_input)
        respones.append(respone)
    
    return respones

if __name__ == "__main__":
    ...