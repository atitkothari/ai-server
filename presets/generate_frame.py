"""Collection of all system prompts for `/generate_frame` API."""

STORYBOARD_PREAMBLE = """\
You"re an experienced story board artist versed in concepts and nitty-gritty details of script writing, creating story boards and mood-boards.

You are given details about a specific frame from a script in form of a dictionary.
Your task is to analyze all that information and produce a description capturing the essential details which will be then used to create an image of that frame. Follow these guidelines:

Focus on below parameters while crafting the description:

--> Subject:
Subject describes what you want to see. It can be simple or detailed. Elements of a subject should be separated by a comma when you want them recognized as an
individual element of the composition.

--> Background/Location:
The background/location describes where the the subject is located. Background/Location is optional.

--> Actions:
Describe the actions, expressions and pose of the characters appearing in the frame. Use modifiers and adjectives to describe it.

--> Camera Angles and Shot types:
Include a specific camera angle and shot type i.e. wide angle shot, full body shot, establishing shot, etc. based on the information you have about the frame. Make sure to include
atleast either camera angle or shot type in the description.

Analyze all the given frame and output only single description covering all these characteristics in less than 40 words. Add the braces `(())` when you want to enhance weightage on any
specific part of the description. Look at the below samples to get some idea but do not blindly copy them:

Here are some sample descriptions considering all these characteristics:
```
closeup portrait of 1 Persian princess, royal clothing, makeup, jewelry, wind-blown long hair, symmetric, desert, ((sands, dusty and foggy, sand storm, winds)) bokeh, depth of field, centered
```
```
Batman in a white color bat suit, covered in snow, in Antarctica, full body, ice and snow background, heavy snowfall.
```
```
photo of a man in the desert the style of realistic hyper-detailed portraits, transparent sunglasses, detailed facial features, dry, heat exhaustion cityscape, metallic ethereal Ian, eye-catching detail, blink-and-you-miss-it-detail.
```

{% if SAMPLE_PROMPT != "" %}
Here are some sample descriptions considering all these characteristics:
```
closeup portrait of 1 Persian princess, royal clothing, makeup, jewelry, wind-blown long hair, symmetric, desert, ((sands, dusty and foggy, sand storm, winds)) bokeh, depth of field, centered
```
{% endif %}"""


COMIC_PREAMBLE = """
You are a skilled prompt creator with strong attention to detail and creativity. Your task is to develop a comprehensive and visually engaging prompt for generating comic book panels using SDXL.

The user will provide you with details about the panel in the below format:
{
    "description": "",  # This is the overall description of the panel.
    "Character 1": "",
    "Character 2": "",
    ...  # These will be the character dilouges
    "location": "",  # This will be the location for the panel.
    "character_clothing": {  # Per character clothing for the panel.
        "Character 1": "",
        "Character 2": "",
    },
    "character_expressions": {  # Per character expressions for the panel.
        "Character 1": "",
        "Character 2": "",
    },
    "shot_type": "MEDIUM_SHOT"
}


Your task is to then follow the below steps:
1) Analyze the panel JSON provided.
2) Carefully consider each character's physical appearance, including clothing, hairstyle, and facial expressions to convey emotion and mood when designing the prompt.
3) Ensure all characters mentioned in the JSON are included in the generated prompt.
4) Reflect the atmosphere and tone of the panel.
5) The output prompt length should not exceed 50 words, accurately representing the given JSON.
6) Pay special attention to the setting's parameters. Character and setting guidelines:
    - Keep backgrounds simple and uncluttered.
    - Emphasize key environmental elements only.
    - Ensure character details are clear and precise.
7) Refer to the provided examples for guidance:
    - In a city park, a young woman (red saree)++ sits alone. Nearby, a woman (yellow dress)++ laughs, while another (denim jacket)++ tosses leaves playfully.
    - In a cozy café, a woman (brown shirt)+, (sipping coffee)+ reads, her friend (black t-shirt)+, (sketching)+ nearby as a barista serves pastries at the counter.
    - At a rainy bus stop, a woman (white dress)++, (holding a letter)+ waits anxiously, while another (green raincoat)+ checks her watch, and two friends chat under an umbrella.
    The + indicates that the model should focus more on that specific part of the prompt.

Ensure you only output the prompt following the guidelines above and nothing else. Be creative!
"""


styles = {
    "CINEMATIC": {
        "SAMPLE": "",
        "PROMPT": "cinematic still {prompt} . emotional, harmonious, vignette, highly detailed, high budget, bokeh, cinemascope, moody, epic, gorgeous, film grain, grainy",
        "NEGATIVE": "sketch, black and white, anime, cartoon, graphic, text, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured",
    },
    "SKETCH": {
        "SAMPLE": "",
        "PROMPT": "Detailed Pencil Sketch, {prompt}, strokes, black and white drawing, graphite drawing",
        "NEGATIVE": "ugly, deformed, noisy, blurry, low contrast",
    },
    "VECTOR_ART": {
        "SAMPLE": "",
        "PROMPT": "Simple Vector Art, {prompt}, 2D flat, simple shapes, minimalistic, professional graphic, flat color, high contrast, Simple Vector Art",
        "NEGATIVE": "ugly, deformed, noisy, blurry, low contrast",
    },
    # "ANIME": {
    #     "SAMPLE": "",
    #     "PROMPT": "anime artwork illustrating {prompt}. created by japanese anime studio. highly emotional. best quality, high resolution",
    #     "NEGATIVE": "low quality, low resolution",
    # },
    "DOODLE": {
        "SAMPLE": "",
        "PROMPT": "Doodle Art Style, {prompt}, drawing, freeform, swirling patterns, doodle art style, colorful",
        "NEGATIVE": "noir, sketch, ugly, deformed, noisy, blurry, low contrast",
    },
    "WATERCOLOR": {
        "SAMPLE": "",
        "PROMPT": "Watercolor style painting, {prompt}, visible paper texture, colorwash, watercolor",
        "NEGATIVE": "ugly, deformed, noisy, blurry, low contrast, photo, realistic",
    },
    "COLOR_SKETCH": {
        "SAMPLE": "",
        "PROMPT": "Colored Pencil Art, {prompt}, colored pencil strokes, light color, visible paper texture, colored pencil art",
        "NEGATIVE": "ugly, deformed, noisy, blurry, low contrast",
    },
    "ADORABLE_3D": {
        "SAMPLE": "",
        "PROMPT": "Adorable 3D Character, {prompt}, 3D render, adorable character, 3D art",
        "NEGATIVE": "ugly, deformed, noisy, blurry, low contrast, grunge, sloppy, unkempt, photograph, photo, realistic",
    },
    "MANGA_COMIC": {
        "SAMPLE": "",
        "PROMPT": "Japanese manga-style illustration, {prompt}, clean black ink lines, grayscale or limited color palette, expressive characters with large eyes, dynamic action lines, speed lines for movement, detailed backgrounds, extreme close-ups, varied panel layouts, sound effect text, emotion symbols",
        "NEGATIVE": "western comic style, full color, photorealistic, 3D rendering, watercolor, oil painting, ugly, deformed, low quality, blurry",
    },
    "ANIME_COMIC": {
        "SAMPLE": "",
        "PROMPT": "High-quality anime comic illustration, {prompt}, vibrant saturated colors, clean bold outlines, large expressive eyes, colorful hair, dramatic lighting effects, action lines, detailed clothing folds, beautiful backgrounds, dynamic poses, emotional expressions, sparkles and visual effects",
        "NEGATIVE": "realistic, photorealistic, western comic style, sketchy, rough lines, dull colors, overly detailed faces, gritty, ugly, deformed, low quality, blurry, watercolor, oil painting",
    },
    "ANIME_COMIC_MUTED": {
        "SAMPLE": "",
        "PROMPT": "Soft anime comic illustration, {prompt}, pastel color palette, gentle lighting, delicate linework, large dreamy eyes, flowing hair, slice-of-life atmosphere, detailed soft backgrounds, school setting, gentle expressions, cherry blossoms, subtle visual effects",
        "NEGATIVE": "dark themes, harsh lighting, rough lines, western style, realistic, gritty, ugly, deformed, low quality, blurry, oversaturated colors",
    },
    "DIGITAL_PAINTING": {
        "SAMPLE": "",
        "PROMPT": "Hyper-realistic digital painting, {prompt},  ultra-detailed skin textures, dramatic lighting, cinematic composition, photorealistic quality, subtle comic outlines, vibrant colors",
        "NEGATIVE": "cartoon, anime, sketch, low quality, blurry, rough, simplistic, flat colors, black and white, monochrome, ugly, deformed, extra organs, bad quality, realistic, cinematic, distorted mouth, unrealistic lips, misshapen teeth",
    },
    "FLUX_COMIC": {
        "SAMPLE": "",
        "PROMPT": "detailed illustrated scene, {prompt}, clean line art, expressive characters, vibrant and warm color palette, soft shading, natural lighting, storytelling composition, scenic background, cohesive color scheme, dynamic poses, crisp and sharp images",
        "NEGATIVE": "disfigured, unrealistic lips, misshapen teeth, unfinished face, monochrome, sketchy, low quality, blurry, rough, abstract, low contrast, ugly, deformed, pixelated, extra organs, bad quality, distorted mouth, overly stylized, unfinished",
    },
    # "MYTHOLOGY": {
    #     "SAMPLE": "",
    #     "PROMPT": "Clear mythological comic scene, {prompt}, legendary heroes and gods, clean divine symbols, focused magical effects, flowing robes, clear facial features, simplified ancient architecture, balanced composition, mythical creatures, clear storytelling elements, glowing auras, recognizable mythological elements, crisp and sharp images",
    #     "NEGATIVE": "overcrowded scenes, cluttered details, overly complex designs, modern elements, busy backgrounds, excessive ornaments, confusing layouts, low quality, blurry, anatomically incorrect"
    # },
    "DARK": {
        "SAMPLE": "",
        "PROMPT": "Dark comic frame, {prompt}, dark and muted color palette, stern yet determined expression, gritty comic-style art with a focus on detailed textures and shading, eerie atmosphere, and subtle earthy tones with a slight illustrative touch.",
        "NEGATIVE": "overly realistic, black and white image, soft color tones, hyper-realistic disfigurement, exaggerated features, misshapen anatomy, completely dark scenes, pure black shadows, invisible details, overly bright, wholesome scenes, low quality, blurry, deformed anatomy, oversaturated colors, anime styles, photographic realism, text or logos in the image",
    },
    # "DARK": {
    #     "SAMPLE": "",
    #     "PROMPT": "Dark, moody, {prompt}, contemporary urban Indian aesthetic, modern minimalist design elements, subtle cultural motifs, clean, modern color palette, sleek character designs, urban/contemporary environments, refined details and textures, balanced composition",
    #     "NEGATIVE": "No ancient Indian elements, no rural/village settings, no heavy traditional jewelry or ornaments, no photorealism, no black and white/monochrome, no harsh/rough elements, no traditional/classical art styles, technical flaws to avoid, no ornate patterns or excessive decoration",
    # },
    "ANIME": {
        "SAMPLE": "",
        "PROMPT": "Anime-style illustration, {prompt}, soft color palette with pastel undertones, large expressive eyes with intricate iris details, warm and immersive color composition, dynamic facial expressions with emotional depth, backgrounds with painterly details and soft focus, exaggerated anime-style proportions, whimsical and magical visual elements, consistent anime aesthetics throughout",
        "NEGATIVE": "Harsh digital rendering, neon colors, overly saturated tones, photorealistic textures, flat lighting, sharp geometric edges, lack of emotional depth, cluttered backgrounds, uniform character designs, non-anime proportions",
    },
    "GHIBLI_COMIC": {
        "SAMPLE": "",
        "PROMPT": "detailed illustrated scene, {prompt}, Studio Ghibli inspired art style, Studio Ghibli's signature environmental details, soft natural lighting, expressive characters, gentle color palette, crisp and sharp images",
        "NEGATIVE": "low quality, blurry, oversaturated, CGI elements, heavy outlines, artificial lighting, photorealistic, 3D rendered, harsh shadows, CGI elements, flat coloring, generic manga style, busy backgrounds, oversaturated colors, sharp contrasts",
    },
    "MOODY_EARTHY": {
        "SAMPLE": "",
        "PROMPT": "Dark comic frame, {prompt}, stern yet determined expression, dark yet muted color tones, gritty art style with a focus on detailed textures and shading, eerie atmosphere with a subtle earthy tone.",
        "NEGATIVE": "Black and white image, muted color tones, realistic disfigurement, unrealistic lips, misshapen teeth, unfinished face, completely dark scenes, pure black shadows, invisible details, overly bright, cute style, wholesome scenes, low quality, blurry, deformed anatomy, oversaturated colors, cartoonish or anime styles, text or logos in the image",
    },
    "ROMANTIC_REALISM": {  
        "SAMPLE": "",  
        "PROMPT": "Boldly outlined comic frame, {prompt}, vibrant romantic comic style, warm and dynamic color palette, expressive and exaggerated character design, intricate and colorful architectural elements reflecting Delhi's blend of history and modernity, lush and vivid backgrounds, dramatic and dynamic lighting, heightened emotional expression, emphasis on cultural elements and personal adventure.",  
        "NEGATIVE": "Flat and dull colors, overly simplistic backgrounds, lack of contrasts, overly simplistic expressions, lack of dynamic features, absence of cultural references, low quality, pixelation, absence of vibrant architecture, monochrome."  
    },
    "DARK_FANTASY": {
        "SAMPLE": "",
        "PROMPT": "Enchanting comic visuals, {prompt}, mystical surrealism style, vibrant yet earthy color palette, intricate traditional Indian motifs, ethereal and otherworldly atmosphere, fluid linework with a touch of divine energy, dynamic compositions capturing nature's fury and serenity, detailed textures evoking ancient carvings, balance between chaos and tranquility.",
        "NEGATIVE": "Flat colors, heavy outlines, modern urban settings, simplistic designs, lack of cultural elements, cartoonish expressions, static poses, low quality, blurred details, generic fantasy aesthetic."
    }
    # "ACTION": {
    #     "SAMPLE": "",
    #     "PROMPT": "Dynamic action comic scene, {prompt}, high-speed motion blur, dramatic camera angles, crisp and sharp images",
    #     "NEGATIVE": "disfigured, unrealistic lips, misshapen teeth, unfinished face, slice of life, dull lighting, flat compositions, weak line work, low energy, blurry action, deformed anatomy, low quality",
    # },
    # "ROMANTIC": {
    #     "SAMPLE": "",
    #     "PROMPT": "dreamy illustrated scene, {prompt}, clean line art, expressive characters, cinematic framing, intimate composition, warm and diffused lighting, soft shading, storytelling composition, scenic background, cohesive color scheme, dynamic poses, crisp and sharp images",
    #     "NEGATIVE": "harsh shadows, overly dramatic, disfigured, dark tones, rough textures, unrealistic lips, misshapen teeth, unfinished face, monochrome, sketchy, low quality, blurry, rough, abstract, low contrast, ugly, deformed, pixelated, extra organs, bad quality, distorted mouth, overly stylized, unfinished",
    # },
    # "ADVENTURE": {
    #     "SAMPLE": "",
    #     "PROMPT": "epic illustrated landscape, {prompt}, expansive scenery, bold color contrasts, adventurous composition, rugged textures, atmospheric perspective, natural elements, cinematic lighting, story-driven details, crisp and sharp images",
    #     "NEGATIVE": "disfigured, unrealistic lips, misshapen teeth, unfinished face, boring composition, flat colors, dull tones, lack of detail, blurry, static poses, overly cluttered, low contrast, sketchy lines, overly simplistic backgrounds, uninspired, low resolution"
    # },
    # "THRILLER": {
    #     "SAMPLE": "",
    #     "PROMPT": "tense illustrated scene, {prompt}, moody and dramatic lighting, sharp contrasts, dark and muted color palette, intense expressions, cinematic composition, eerie atmosphere, mysterious shadows, detailed textures, dynamic angles, crisp and sharp images",
    #     "NEGATIVE": "disfigured, unrealistic lips, misshapen teeth, unfinished face, bright and cheery, soft pastels, overly simplistic, flat lighting, low detail, blurry, unrealistic proportions, colorful palette, lack of tension, cartoonish elements, disjointed"
    # },
}


genres = {
    "INDIAN": {
        "SAMPLE": "",
        "PROMPT": "Bollywood influence, rich cultural symbols, indian people",
        "NEGATIVE": "white people, western people, European, ugly, deformed, noisy, blurry, artificial, cartoonist, low quality, distorted, pixelated, generic, irrelevant, futuristic, modern, abstract, monochrome, minimalist, non-Indian setting",
    },
    "HOLLYWOOD": {
        "SAMPLE": "",
        "PROMPT": "Hollywood movie scene, dramatic lighting, popular actors, high production value, American cinema",
        "NEGATIVE": "low budget, amateurish, foreign film style, experimental, avant-garde, documentary style",
    },
    "JAPANESE": {
        "SAMPLE": "",
        "PROMPT": "Japanese style, live-action film still, dramatic lighting, Japanese settings, Kurosawa-inspired",
        "NEGATIVE": "anime, manga, cartoon, illustration, animated, unrealistic, western style, Hollywood, ugly, deformed, noisy, blurry, low quality, distorted, pixelated",
    },
}


shot_types = {
    "WIDE_SHOT": {
        "PROMPT": "Wide angle view, full scene visible, establishing shot, panoramic, broad perspective, expansive view",
        "NEGATIVE": "cropped, close-up, restricted view",
    },
    "MEDIUM_SHOT": {
        "PROMPT": "Medium shot, subject from knees or waist up, balanced framing, clear view of subject and some surroundings",
        "NEGATIVE": "extreme close-up, full body shot, wide angle",
    },
    "CLOSE_UP": {
        "PROMPT": "Close-up shot. intimate framing, focus on details, emphasis on facial features or specific elements",
        "NEGATIVE": "full body, wide angle, distant shot",
    },
    "EXTREME_CLOSE_UP": {
        "PROMPT": "Extreme close-up, macro shot, intricate details visible, filling the entire frame with a small part of the subject",
        "NEGATIVE": "full body, wide shot, distant view",
    },
}
