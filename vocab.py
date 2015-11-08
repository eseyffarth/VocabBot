import tweepy
import vocabconfig
import re
import random


def login():
    # for info on the tweepy module, see http://tweepy.readthedocs.org/en/
    # Authentication is taken from deutsch_config.py
    consumer_key = vocabconfig.consumer_key
    consumer_secret = vocabconfig.consumer_secret
    access_token = vocabconfig.access_token
    access_token_secret = vocabconfig.access_token_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def react_to_mention(api, mention):
    POSITIVE_ANSWER = "That's correct!"
    NEGATIVE_ANSWER = "No, that's not right."
    NEW_ENTRY_ANSWER = "Added new vocab entry:"
    KNOWN_ENTRY_ANSWER = "I already knew that!"

    BOT_TWITTER_HANDLE = "frenchvocabbot"
    CURRENT_CORRECT_ANSWER_FILENAME = "currentanswer.txt"
    DICTIONARY_FILENAME = "frenchvocabdata.txt"

    id = mention.id
    name = mention.user.screen_name
    new_entry = re.match("^\@"+BOT_TWITTER_HANDLE+"\s+\+\s+(.*)$", mention.text, re.IGNORECASE)
    if new_entry:
        with open(DICTIONARY_FILENAME, "r+", encoding="utf8") as data:
            if new_entry.group(1) not in data.read():
                print(new_entry.group(1), file=data)
                out = "@{} {} {}".format(name, NEW_ENTRY_ANSWER, new_entry.group(1))
            else:
                out = "@{} {}".format(name, KNOWN_ENTRY_ANSWER)
        api.update_status(status=out, in_reply_to_status_id=id)
    else:
        user_answer = re.match("^\@"+BOT_TWITTER_HANDLE+"\s+(a|b|c)\)?$", mention.text, re.IGNORECASE)
        if user_answer:
            with open(CURRENT_CORRECT_ANSWER_FILENAME, "r", encoding="utf8") as correct_answer:
                correct_answer = correct_answer.read().strip()
                if user_answer.group(1).lower() == correct_answer.lower():
                    out = "@{} {}".format(name, POSITIVE_ANSWER)
                else:
                    out = "@{} {}".format(name, NEGATIVE_ANSWER)
                api.update_status(status=out, in_reply_to_status_id=id)
    return

def look_for_mentions(api):
    LAST_PROCESSED_MENTION_ID_FILENAME = "vocabmentions"

    with open(LAST_PROCESSED_MENTION_ID_FILENAME, "r+") as data:
        last_mention_id = int(data.read().strip())

    my_followers = [s.screen_name for s in api.followers()]

    largest_mention_id = last_mention_id
    for mention in api.mentions_timeline():
        if mention.id <= last_mention_id:
            break

        if mention.user.screen_name in my_followers:
            react_to_mention(api, mention)

            if largest_mention_id <= mention.id:
                largest_mention_id = mention.id

    with open(LAST_PROCESSED_MENTION_ID_FILENAME, "w") as data:
        print(largest_mention_id, file=data)
    return

def entrypoint():
    api = login()
    look_for_mentions(api)

def ask():
    VOCAB_DATA_FILENAME = "frenchvocabdata.txt"
    CURRENT_CORRECT_ANSWER_FILENAME = "currentanswer.txt"

    api = login()
    tweetlen = 141
    with open(VOCAB_DATA_FILENAME, "r", encoding="utf8") as dictionary:
        while tweetlen > 140:
            questions = [l for l in dictionary.readlines() if len(l.strip()) > 0]
            question_firstlang = random.randint(0, 1)
            data = {}
            if question_firstlang == 0:
                for line in questions:
                    line = line.split("=")
                    data[line[0].strip()] = line[1].strip()
            else:
                for line in questions:
                    line = line.split("=")
                    data[line[1].strip()] = line[0].strip()

            question = random.choice(list(data.keys()))
            correct_answer = data[question]
            wrong_answer_1 = correct_answer
            wrong_answer_2 = correct_answer
            while wrong_answer_1 == correct_answer:
                wrong_answer_1 = random.choice(list(data.values()))
            while wrong_answer_2 == correct_answer or wrong_answer_2 == wrong_answer_1:
                wrong_answer_2 = random.choice(list(data.values()))
            # we are now sure that the two wrong answers are something else than the correct answer,
            # and also different from each other
            choices = [correct_answer, wrong_answer_1, wrong_answer_2]
            random.shuffle(choices)
            out = "{} = ... \na) {}\nb) {}\nc) {}".format(question, choices[0], choices[1], choices[2])
            print(out)
            tweetlen = len(out)

        api.update_status(status=out)
        with open(CURRENT_CORRECT_ANSWER_FILENAME, "w", encoding="utf8") as answer:
            correct_index = ["a", "b", "c"][choices.index(correct_answer)]
            print(correct_index, file=answer)
    return
