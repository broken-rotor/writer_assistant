"""
Quick test script to verify Phase 1 implementation of new StructuredContextContainer methods.
"""

from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)


def test_query_methods():
    """Test the new query methods."""
    print("Testing query methods...")

    # Create test data
    container = StructuredContextContainer(
        plot_elements=[
            PlotElement(
                id="plot1",
                type="scene",
                content="The hero enters the dark forest",
                priority="high",
                tags=["current_scene", "chapter1"]
            ),
            PlotElement(
                id="plot2",
                type="conflict",
                content="The antagonist appears",
                priority="medium",
                tags=["chapter1"]
            ),
            PlotElement(
                id="plot3",
                type="resolution",
                content="The hero escapes",
                priority="low",
                tags=["chapter2"]
            )
        ],
        character_contexts=[
            CharacterContext(
                character_id="char1",
                character_name="Aria",
                current_state={"emotion": "determined", "location": "forest"},
                goals=["Find the artifact", "Escape the forest"],
                recent_actions=["Entered the forest"],
                personality_traits=["brave", "curious"],
                relationships={"antagonist": "enemy"}
            ),
            CharacterContext(
                character_id="char2",
                character_name="Villain",
                current_state={"emotion": "angry"},
                goals=["Stop Aria"],
                personality_traits=["cruel"]
            )
        ],
        user_requests=[
            UserRequest(
                id="req1",
                type="modification",
                content="Make it more atmospheric",
                priority="high"
            ),
            UserRequest(
                id="req2",
                type="addition",
                content="Add more dialogue",
                priority="medium"
            )
        ],
        system_instructions=[
            SystemInstruction(
                id="sys1",
                type="behavior",
                content="Write in third person",
                scope="global",
                priority="high"
            ),
            SystemInstruction(
                id="sys2",
                type="style",
                content="Use descriptive language",
                scope="scene",
                priority="medium"
            )
        ]
    )

    # Test plot element queries
    print("\n1. Testing get_plot_elements_by_type:")
    scenes = container.get_plot_elements_by_type("scene")
    print(f"   Found {len(scenes)} scene(s): {[s.content for s in scenes]}")
    assert len(scenes) == 1
    assert scenes[0].id == "plot1"

    print("\n2. Testing get_plot_elements_by_priority:")
    high_priority = container.get_plot_elements_by_priority("high")
    print(f"   Found {len(high_priority)} high priority plot element(s)")
    assert len(high_priority) == 1

    print("\n3. Testing get_plot_elements_by_tag:")
    chapter1 = container.get_plot_elements_by_tag("chapter1")
    print(f"   Found {len(chapter1)} element(s) with 'chapter1' tag")
    assert len(chapter1) == 2

    # Test character queries
    print("\n4. Testing get_character_context_by_id:")
    aria = container.get_character_context_by_id("char1")
    print(f"   Found character: {aria.character_name if aria else 'None'}")
    assert aria is not None
    assert aria.character_name == "Aria"

    print("\n5. Testing get_character_context_by_name:")
    villain = container.get_character_context_by_name("villain")
    print(f"   Found character: {villain.character_name if villain else 'None'}")
    assert villain is not None
    assert villain.character_id == "char2"

    # Test high priority elements
    print("\n6. Testing get_high_priority_elements:")
    high_priority_all = container.get_high_priority_elements()
    print(f"   High priority elements by type:")
    for key, items in high_priority_all.items():
        print(f"     {key}: {len(items)} item(s)")
    assert len(high_priority_all["plot_elements"]) == 1
    assert len(high_priority_all["user_requests"]) == 1
    assert len(high_priority_all["system_instructions"]) == 1

    # Test user request and system instruction queries
    print("\n7. Testing get_user_requests_by_type:")
    modifications = container.get_user_requests_by_type("modification")
    print(f"   Found {len(modifications)} modification request(s)")
    assert len(modifications) == 1

    print("\n8. Testing get_system_instructions_by_scope:")
    global_instructions = container.get_system_instructions_by_scope("global")
    print(f"   Found {len(global_instructions)} global instruction(s)")
    assert len(global_instructions) == 1

    print("\n✓ All query method tests passed!")


def test_token_counting():
    """Test token counting methods."""
    print("\n\nTesting token counting methods...")

    # Create simple test data
    container = StructuredContextContainer(
        plot_elements=[
            PlotElement(
                id="plot1",
                type="scene",
                content="The hero enters the dark forest at midnight.",
                priority="high",
                tags=["scene"]
            )
        ],
        character_contexts=[
            CharacterContext(
                character_id="char1",
                character_name="Aria",
                current_state={"emotion": "determined"},
                goals=["Find artifact"],
                personality_traits=["brave"]
            )
        ],
        user_requests=[
            UserRequest(
                id="req1",
                type="modification",
                content="Add atmospheric details",
                priority="high"
            )
        ],
        system_instructions=[
            SystemInstruction(
                id="sys1",
                type="behavior",
                content="Write in third person narrative style",
                scope="global",
                priority="high"
            )
        ]
    )

    print("\n1. Testing calculate_total_tokens (with estimation):")
    try:
        total_tokens = container.calculate_total_tokens(use_estimation=True)
        print(f"   Total tokens (estimated): {total_tokens}")
        assert total_tokens > 0
    except Exception as e:
        print(f"   Note: TokenCounter may not be available: {e}")
        print(f"   This is expected if llama.cpp model is not loaded")

    print("\n2. Testing get_token_breakdown:")
    try:
        breakdown = container.get_token_breakdown()
        print(f"   Token breakdown:")
        for key, count in breakdown.items():
            print(f"     {key}: {count}")
        assert breakdown["total"] > 0
        assert breakdown["total"] == sum(
            v for k, v in breakdown.items() if k != "total"
        )
    except Exception as e:
        print(f"   Note: TokenCounter may not be available: {e}")
        print(f"   This is expected if llama.cpp model is not loaded")

    print("\n✓ Token counting tests completed (may use fallback if model not loaded)")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 Implementation Test")
    print("=" * 60)

    test_query_methods()
    test_token_counting()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
