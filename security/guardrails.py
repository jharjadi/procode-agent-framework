def validate_input(context):
    # Simple input validation: must have non-empty text
    text = getattr(context.input, "text", None)
    return isinstance(text, str) and len(text.strip()) > 0

def validate_output(output):
    # Simple output validation: must be a non-empty string
    return isinstance(output, str) and len(output.strip()) > 0
