# -*- coding: utf-8 -*-
"""
Script + scene breakdown for The One Minute Channel.
Topic chosen: The Anglo-Zanzibar War — the shortest war in recorded history (38 minutes).
"""

TITLE = "The 38-Minute War"

CANVA_DIR = "/home/claude/one-minute-video/canva_previews"
INTRO_IMAGE = f"{CANVA_DIR}/intro.jpg"
OUTRO_IMAGE = f"{CANVA_DIR}/outro.jpg"

SCENES = [
    {
        "caption": "On August 27th, 1896,\nthe shortest war in\nrecorded history began.",
        "narration": "On August 27th, 1896, the shortest war in recorded history began.",
        "bg_image": f"{CANVA_DIR}/scene1_clock.jpg",
        "motion_prompt": "Slow cinematic push-in on an antique wall clock, the second hand ticking steadily, dust motes drifting in a shaft of light.",
    },
    {
        "caption": "Sultan Hamad bin Thuwaini\nof Zanzibar had just died —\nand his cousin seized the palace.",
        "narration": "Sultan Hamad bin Thuwaini of Zanzibar had just died, and his cousin Khalid bin Barghash seized the palace without British permission.",
        "bg_image": f"{CANVA_DIR}/scene2_palace.jpg",
        "motion_prompt": "Slow lateral drift past an ornate coastal palace facade, tension in the air, soft breeze moving palm fronds.",
    },
    {
        "caption": "Britain gave an ultimatum:\nstand down by 9 AM,\nor be fired upon.",
        "narration": "Britain, which controlled Zanzibar as a protectorate, gave an ultimatum: stand down by nine A M, or be fired upon.",
        "bg_image": f"{CANVA_DIR}/scene3_scroll.jpg",
        "motion_prompt": "Slow push-in on an unrolling official scroll document, parchment edges gently curling in a light breeze.",
    },
    {
        "caption": "At 9:02 AM,\nRoyal Navy ships\nopened fire on the palace.",
        "narration": "At nine-oh-two A M, Royal Navy ships opened fire on the palace.",
        "bg_image": f"{CANVA_DIR}/scene4_ship.jpg",
        "motion_prompt": "Royal Navy warship at anchor, gentle rocking on the swell, smoke beginning to rise from a gun turret, choppy sea motion.",
    },
    {
        "caption": "By 9:40 AM — just 38\nminutes later — the palace\nhad surrendered.",
        "narration": "By nine-forty A M, just thirty-eight minutes later, the palace had surrendered. The war was over.",
        "bg_image": f"{CANVA_DIR}/scene5_flag.jpg",
        "motion_prompt": "A white flag being slowly raised and settling into a gentle wave in the wind against a calm sky.",
    },
    {
        "caption": "The Anglo-Zanzibar War remains\nthe shortest war\never recorded.",
        "narration": "The Anglo-Zanzibar War remains the shortest war ever recorded — start to finish, in well under an hour.",
        "bg_image": f"{CANVA_DIR}/scene6_trophy.jpg",
        "motion_prompt": "Slow orbit around an engraved trophy or plaque catching warm light, subtle rack focus, dust motes drifting.",
    },
]
