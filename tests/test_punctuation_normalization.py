import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.llm.post_process import normalize_sentence_frame_punctuation


def test_normalization():
    test_json = {
        "days": {
            "monday": {
                "sentence_frames": [
                    {
                        "frame_type": "frame",
                        "english": "This is a frame",
                        "portuguese": "Isto é um frame"
                    },
                    {
                        "frame_type": "frame",
                        "english": "This frame ends with period.",
                        "portuguese": "Este frame termina com ponto."
                    },
                    {
                        "frame_type": "stem",
                        "english": "This is a stem ",
                        "portuguese": "Isto é um stem "
                    },
                    {
                        "frame_type": "open_question",
                        "english": "Is this a question",
                        "portuguese": "Isto é uma pergunta"
                    },
                    {
                        "frame_type": "open_question",
                        "english": "Is this a question?",
                        "portuguese": "Isto é uma pergunta?"
                    },
                    {
                        "frame_type": "frame",
                        "english": "This has wrong punctuation?",
                        "portuguese": "Isto tem pontuação errada?"
                    }
                ]
            }
        }
    }
    
    normalized = normalize_sentence_frame_punctuation(test_json)
    
    frames = normalized["days"]["monday"]["sentence_frames"]
    
    # Assertions
    assert frames[0]["english"] == "This is a frame."
    assert frames[0]["portuguese"] == "Isto é um frame."
    
    assert frames[1]["english"] == "This frame ends with period."
    assert frames[1]["portuguese"] == "Este frame termina com ponto."
    
    assert frames[2]["english"] == "This is a stem."
    assert frames[2]["portuguese"] == "Isto é um stem."
    
    assert frames[3]["english"] == "Is this a question?"
    assert frames[3]["portuguese"] == "Isto é uma pergunta?"
    
    assert frames[4]["english"] == "Is this a question?"
    assert frames[4]["portuguese"] == "Isto é uma pergunta?"
    
    assert frames[5]["english"] == "This has wrong punctuation."
    assert frames[5]["portuguese"] == "Isto tem pontuação errada."
    
    print("All tests passed!")

if __name__ == "__main__":
    try:
        test_normalization()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
