from importlib import resources
import requests
import json
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def llama3(request):
    data = json.loads(request.body)
    message = data.get("message", "")

    # Retrieve chat history from Django session
    session = request.session
    chat_history = session.get("chat_history", [])

    print("\033c", end="")  # Clears the screen
    print("\n")
    print("=========")
    print(chat_history)
    print("=========")

    chat_history.append({"role": "user", "content": message})

    url = "http://host.docker.internal:11434/api/chat"
    headers = {"Content-Type": "application/json"}

    data = {
        "model": "llama3",
        "messages": chat_history,
        "stream": True,
    }

    # Variable to store the AI's full response
    ai_response_content = []

    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        def stream_response():
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        json_chunk = json.loads(chunk.decode("utf-8"))
                        chunk_content = json_chunk.get("content", "")
                        json_string = json.dumps(json_chunk) + "\n"

                        # Store each chunk in the AI response list
                        ai_response_content.append(chunk_content)

                        yield json_string
                    except json.JSONDecodeError:
                        print("Invalid JSON chunk detected")
                        yield json.dumps({"error": "Invalid JSON chunk"}) + "\n"

        # After streaming completes, store the full AI response
        full_ai_response = "".join(ai_response_content)
        chat_history.append({"role": "assistant", "content": full_ai_response})

        # Save updated chat history back to the session
        session["chat_history"] = chat_history
        session.modified = True

        return StreamingHttpResponse(stream_response(), content_type="text/plain")

    except requests.exceptions.RequestException as e:
        return StreamingHttpResponse(
            f"Request failed: {str(e)}", content_type="text/plain"
        )

    # Prompt:


#     """
#     I'd like you to become a chatbot that helps undergraduate students improve their metacognitive strategies in their self-regulated learning activities. I'll provide the rules for how you should interact with the students

#     Here are the rules:
# 1. Students are divided into five levels based on analysis of their past user logs on the education portal website. Each student's metacognitive score depends on how complex, diverse, consistent, and frequent they interact with the website and study materials. Here are the descriptions for each level:
# - Level 1 (low): the student has never performed any metacognitive strategies.
# - Level 2 (medium-to-low): the student has, in the past, performed a limited subset of metacognitive regulations (planning, monitoring, and/or evaluation), though not in a way that is suitable for the context.
# - Level 3 (medium): the student has, in the past, performed all three types of metacognitive strategies, though not in a way that is suitable for the context or produces desired results.
#  - Level 4 (medium-to-high): the student consistently and frequently performs all three types of metacognitive strategies, though not in a way that is suitable for the context.
# - Level 5 (high): the student consistently and frequently performs all three types of metacognitive strategies in combinations that are suitable for their contexts.
# 2. Each level of students need different types of guidance to improve their metacognitive regulations. Here is how you should interact with them:
# - Level 1: focus your advice on inducing student’s motivation to engage with the materials and to self-regulate their studies. To do this, you may need to ask some diagnosing questions to figure out what the student’s goals and values are and use that to develop strategies to increase the student’s motivation.
# - Level 2: focus on providing the student with basic metacognitive or self-regulated strategies, expanding their repertoires of techniques they can use. However, you should not give them a long list. Instead, be very specific with your suggestion and only provide information that is relevant to their current goal or struggle. Your suggestion should be straightforward and actionable.
# - Level 3: focus on teaching the students how to apply metacognitive strategies in a way that is suitable for their contexts. Ask diagnosing questions to understand their problems and give specific, straightforwardly actionable suggestions.
# - Level 4: focus on teaching the students how to apply metacognitive strategies in a way that is suitable for their contexts. However, instead of giving them actionable advice like Level 3, you should scaffold and ask leading questions to let the student arrive at the solution by themselves, so that in the future they can figure out what to do on their own.
# - Level 5: there is nothing specific to focus on with Level 5. When they come to you with a problem regarding their metacognitive regulation, you should act like a peer and discuss with them as equals to arrive together at a solution. This means that you may probe them about what their problems are, what they have tried, why their past strategies don’t work, what are other options they can explore.
# 3. When talking to the student, do not ask many probing/diagnosing questions in one go, as they may be overwhelming for the student. Ask one question at a time, and after the student answers, you can follow-up.
#     """


# TODO =========
# 1. Fix the chat_history. Response bot is not working, so get that working

# Does changing urls are restarting the page reset the django session? Need to figure this out, and make it unique to user.ID. How to access the user.ID? I'm so fucking lost.

# 2. Add basic prompting about what the AI should expect to do (just one paragraph
# 3. Try to pass general information to the bot (name for now)?
# 4. Try to find list of coursees they are taking
# 5. Try to find what resources they are able to access.


# ==================================   AGENDA FOR TOMORROW   ================================== #

# Tmmr Morning (prepare for the conversation):
# 1. What have I done?
# - Redesigned the frontend side panel.
# - The chatbot actually works now, albeit it's a bit slow. There were some problems with markdown on the previous model, but that's been fixed with react-markdown.
# - Fixed the pipeline between the backend and frontend (able to transit messages properly without crashing)
# - Added a django session in the backend to store previous chat_messages

# - [ ] Want to finish firt paragraph of prompting = ....
# - [ ] The llama3 chatbot has access to some of the student's information:
#     - Name
#     - List of courses taking
#     - Resources access.
#     - [ ] More about the course information, but not sure how to do that right now.

# 2. What I think we need / what I plan to do?
# - Improve on the prompting for the 3 personas.
# - Need to tell AI to categorize users still.
# - Still need to access some of the information (resources access etc)
# - Anything else???

# 3. Questions / concerns?
# - I have the 3 persona's, which I copied and pasted from the google sheet, but not sure if there's a better way to prompt this.
# - I'm still a bit confused about what the AI should have access to, and how that would help. Does this information help with categorizing the students into priority (low, med, high), or will they use this to offer advice?
# - I'm reading through the google docs and it's a bit confusing to me. It might take a while for me to understand this.
#     - Student scoring?
#     - How does the ai react to different levels of student scoring?
