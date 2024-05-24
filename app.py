import streamlit as st
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler
import os
# Initialize the OpenAI client
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Retrieve assistant and vector store
assistant = client.beta.assistants.retrieve("asst_xGjXM6VQytkJtN5EuD7aBKdl")
vector_store = client.beta.vector_stores.retrieve("vs_Rvf0rhHU795hFWv7HcRl3Hcj")

# Update assistant with the vector store ID


# Streamlit application starts here
def main():
    st.title('Smith & Nephew Question Answering App')
    user_input = st.text_input('Enter your question:', '')
    model_version = st.selectbox('Select the model version:', ['gpt-3.5-turbo', 'gpt-4-turbo'])
    client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        model="gpt-4o",
    )
    if st.button('Submit'):
        if user_input:
            # Create a thread and attach the file to the message
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ]
            )

            class EventHandler(AssistantEventHandler):
                @override
                def on_text_created(self, text) -> None:
                    st.write(f"\nassistant > ", end="", flush=True)

                @override
                def on_tool_call_created(self, tool_call):
                    st.write(f"Tool call: {tool_call.type}")


                @override
                def on_message_done(self, message) -> None:
                    # Handle file search citations
                    message_content = message.content[0].text
                    annotations = message_content.annotations
                    citations = []
                    for index, annotation in enumerate(annotations):
                        message_content.value = message_content.value.replace(
                            annotation.text, "[" + str(index) + "]"
                        )
                        if (file_citation := getattr(annotation, 'file_citation', None)):
                            cited_file = client.files.retrieve(file_citation.file_id)
                            citations.append('[' + str(index) + '] | ' + cited_file.filename)
                    st.write(message_content.value + '\n\n' + '\n'.join(citations))

            with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="You must always quote the original information",
                event_handler=EventHandler(),
            ) as stream:
                stream.until_done()

if __name__ == "__main__":
    main()
