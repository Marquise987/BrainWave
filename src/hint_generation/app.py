import openai
import streamlit as st

from brain_wave import prompt_utils, retrieval_strategies
from brain_wave.prompts import hints as hint_prompts
from streamlit_app import auth_utils, chat_utils, data_utils

SHOW_QUESTION_BANK = False
REQUIRE_AUTHENTICATION = False
QUESTION_SELECTBOX_DEFAULT_STRING = "(Choose a question from a Rori micro-lesson)"
HINT_TYPE_BUTTON_LABELS_MAP = {
    "hint_sequence": "Get a hint sequence",
    #    "slip_correction": "Correct a slip",
    #    "misconception": "Describe a misconception",
    #    "comparative_hint": "Compare this problem to a worked example",
}


def question_selectbox_changed():
    if st.session_state.question_selectbox != QUESTION_SELECTBOX_DEFAULT_STRING:
        display_name = st.session_state.question_selectbox
        question_df = data_utils.load_hint_problem_data()
        selected = question_df[question_df.display_name == display_name]
        assert len(selected) == 1
        selected = selected.iloc[0]
        st.session_state.question_text_area = selected.question
        st.session_state.incorrect_answer_text_input = selected.incorrect_answer
        st.session_state.correct_answer_text_input = selected.answer
        st.session_state.lesson_text_area = selected.lesson_trimmed
        
         # Optionally fill more fields if they exist in the dataframe
        if 'explanation' in selected and not pd.isna(selected.explanation):
            st.session_state.explanation_text_area = selected.explanation
        
        if 'hint' in selected and not pd.isna(selected.hint):
            st.session_state.hint_text_area = selected.hint

        # Optionally log to debug or give user feedback
        print(f"[DEBUG] Loaded question: {selected.display_name}")
        print(f"[DEBUG] Lesson: {selected.lesson_trimmed[:50]}...")


def hint_chat_input_changed():
    st.session_state.hint_chat_input_new_value = st.session_state.hint_chat_input


def hint_type_button_clicked(hint_type: str):
    create_new_hint(hint_type)


def process_hint_query(messages: list[dict]):
    # show the generated prompt if expert controls enabled
    if st.session_state.show_expert_controls:
        with st.expander("Prompt"):
            prompt = prompt_utils.PromptSelector.convert_conversation_to_string(
                st.session_state.hint_prompt_manager.stored_messages,
            )
            prompt = prompt.replace("\n", "\n\n")
            st.markdown(prompt)
    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()
        with st.spinner(""):
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
            )
            assistant_message = completion["choices"][0]["message"]
            assert "role" in assistant_message and "content" in assistant_message
            st.session_state.hint_prompt_manager.add_stored_message(assistant_message)
        response = assistant_message["content"]
        for displayed_message in chat_utils.stream_text_response(response):
            message_placeholder.markdown(displayed_message)

        st.session_state.hint_chat_messages.append(assistant_message)


def create_new_hint(hint_type: str):
    st.session_state.hint_chat_messages = []
    st.session_state.hint_prompt_manager.clear_stored_messages()
    correct_answer = st.session_state.correct_answer_text_input.strip()
    incorrect_answer = st.session_state.incorrect_answer_text_input.strip()
    question = st.session_state.question_text_area.strip()
    lesson = st.session_state.lesson_text_area.strip()
    st.session_state.hint_prompt_manager.get_retrieval_strategy().update_map(
        {
            "question": question,
            "correct_answer": correct_answer,
            "incorrect_answer": incorrect_answer,
            "lesson": lesson,
        },
    )
    intro_messages = hint_prompts.intro_prompts[hint_type]["messages"]
    st.session_state.hint_prompt_manager.set_intro_messages(intro_messages)
    messages = st.session_state.hint_prompt_manager.build_query(None)
    st.session_state.new_hint_request_messages = messages


def process_followup_query(user_query: str):
    user_message = {
        "role": "user",
        "content": user_query,
    }
    st.session_state.hint_chat_messages.append(user_message)
    with st.chat_message("user", avatar=chat_utils.get_avatar("user")):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()

        with st.spinner(""):
            messages = st.session_state.hint_prompt_manager.build_query(user_query)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
            )
            assistant_message = completion["choices"][0]["message"]
            assert "role" in assistant_message and "content" in assistant_message
        response = assistant_message["content"]
        for displayed_message in chat_utils.stream_text_response(response):
            message_placeholder.markdown(displayed_message)

        st.session_state.hint_chat_messages.append(assistant_message)
        st.session_state.hint_prompt_manager.add_stored_message(assistant_message)


def instantiate_session():
    # settings
    setting_defaults = {
        "new_hint_request_messages": None,
        "hint_chat_input_new_value": None,
        "show_expert_controls": False,
    }
    # initialize all values in the settings dict
    # (happens only on the first run each session)
    for key_name, default_value in setting_defaults.items():
        if key_name not in st.session_state:
            st.session_state[key_name] = default_value

    if "hint_prompt_manager" not in st.session_state:
        st.session_state.hint_prompt_manager = prompt_utils.PromptManager()
        slot_map = data_utils.create_hint_default_retrieval_slot_map()
        retrieval_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(slot_map)
        st.session_state.hint_prompt_manager.set_retrieval_strategy(retrieval_strategy)

    if "show_expert_controls" in st.query_params:
        if st.query_params["show_expert_controls"][0].lower() == "true":
            st.session_state.show_expert_controls = True

    if "is_openai_key_set" not in st.session_state or not st.session_state.is_openai_key_set:
        if "openai_api_key" in st.query_params:
            openai.api_key = st.query_params["openai_api_key"]
        else:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.is_openai_key_set = True


def make_sidebar():
    with st.sidebar:
        st.markdown(
            """
### About this demo

This demo was produced with the [Learning Engineering Virtual Institute](https://learning-engineering-virtual-institute.org/) (LEVI)
        in collaboration with [Digital Harbor Foundation](https://digitalharbor.org/),
        [Rising Academies](https://www.risingacademies.com/),
        and [The Learning Agency](https://the-learning-agency.com/).
The primary contributors are [Zachary Levonian](https://levon003.github.io/) and [Owen Henkel](https://www.linkedin.com/in/owenhenkel/).

This demo was made in [Streamlit](https://streamlit.io/). The code and data for this demo are available [on GitHub](https://github.com/DigitalHarborFoundation/BrainWave).

### How does this demo work?

This demo uses [ChatGPT](https://openai.com/chatgpt) to generate hints based on the text you provide in the form.
Specifically, we use the GPT-3.5 model alongside a technical technique called ["retrieval augmented generation"](https://www.promptingguide.ai/techniques/rag) to provide hints that are (hopefully!) appropriate for middle-school math students.

As this is just a demo and it relies on ChatGPT, it will make mistakes! We wouldn't recommend you use this to actually write course content, although if it's helpful to you please let us know.

This demo relies on access to a variety of open-access data sources:
we use sample micro-lessons, problems, and common incorrect answers provided by [Rising Academies](https://www.risingacademies.com/),
a pre-algebra textbook available for free from [OpenStax](https://openstax.org/details/books/prealgebra-2e), and a list of common math misconceptions assembled by [Nancy Otero](https://github.com/creature-ai/math-misconceptions).

Have more questions or comments? Please contact Zach (<zach@levi.digitalharbor.org>) with your thoughts!
        """,
        )


def build_app():
    st.markdown(
        """Generate hints for practice problems, given an incorrect answer.""",
    )
    question_df = data_utils.load_hint_problem_data()
    st.text_area(
        "Write a brief teaching objective in the box below.",
        key="lesson_text_area",
    )
    if SHOW_QUESTION_BANK:
        st.selectbox(
            "Choose a practice problem:",
            [QUESTION_SELECTBOX_DEFAULT_STRING] + question_df.display_name.to_list(),
            key="question_selectbox",
            on_change=question_selectbox_changed,
        )
    st.text_area(
        "Insert practice problem in box below.",
        key="question_text_area",
    )
    c1, c2 = st.columns(2)
    with c1:
        st.text_input(
            "Student's incorrect answer:",
            key="incorrect_answer_text_input",
        )
    with c2:
        st.text_input(
            "Correct answer:",
            key="correct_answer_text_input",
        )
    correct_answer = st.session_state.correct_answer_text_input.strip()
    incorrect_answer = st.session_state.incorrect_answer_text_input.strip()
    are_buttons_enabled = (
        correct_answer != "" and incorrect_answer != "" and st.session_state.question_text_area.strip() != ""
    )
    # if not are_buttons_enabled:
    #    st.warning(
    #        f"Select a practice problem above, then choose one of {len(HINT_TYPE_BUTTON_LABELS_MAP)} hint types.",
    #    )
    if len(correct_answer) > 0 and correct_answer == incorrect_answer:
        st.warning("To generate a hint, the student's answer can't match the correct answer.")
        are_buttons_enabled = False
    # add the hint buttons
    for hint_type, button_label in HINT_TYPE_BUTTON_LABELS_MAP.items():
        st.button(
            button_label,
            key=f"{hint_type}_button",
            on_click=hint_type_button_clicked,
            args=(hint_type,),
            disabled=not are_buttons_enabled,
        )

    if "hint_chat_messages" not in st.session_state:
        st.session_state.hint_chat_messages = []

    # replay history, if there is any
    for message in st.session_state.hint_chat_messages:
        with st.chat_message(message["role"], avatar=chat_utils.get_avatar(message["role"])):
            st.markdown(message["content"])

    if st.session_state.new_hint_request_messages is not None:
        process_hint_query(st.session_state.new_hint_request_messages)
        st.session_state.new_hint_request_messages = None
    elif st.session_state.hint_chat_input_new_value is not None:
        user_query = st.session_state.hint_chat_input_new_value
        st.session_state.hint_chat_input_new_value = None
        process_followup_query(user_query)

    if len(st.session_state.hint_chat_messages) > 0:
        # only display chat input once an initial hint has been generated
        st.chat_input(
            "Ask a follow-up question about the problem",
            key="hint_chat_input",
            on_submit=hint_chat_input_changed,
        )


st.set_page_config(
    page_title="Hint generation with ChatGPT - for math educators",
    page_icon="💡",
)

st.markdown("# Creating math hints with ChatGPT")
make_sidebar()
if not REQUIRE_AUTHENTICATION or auth_utils.check_is_authorized(allow_openai_key=False):
    instantiate_session()
    build_app()
else:
    st.markdown(
        "Thanks for your interest in our demo! The password should have been shared with you alongside the demo link.\n\nPlease contact Zach (<zach@digitalharbor.org>) with any questions about getting access.",
    )
