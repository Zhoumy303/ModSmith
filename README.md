## Overview
<img width="3292" height="1960" alt="image" src="https://github.com/user-attachments/assets/d5156640-6417-4957-aea1-10ef9ab04636" />

ModSmith is an AI-powered Minecraft mod generator. You describe what you want in natural language — "a glowing apple that restores 4 hunger points" — and the system translates your idea into a fully compilable, installable Minecraft Fabric mod.

The core design decouples "user intent" from "code implementation": the LLM only translates natural language into a verifiable JSON blueprint, then deterministic templates generate the actual Java source and resource files. This approach is predictable, verifiable, and rollback-safe. Two layers of verification — compile-time and runtime — ensure the generated mod actually works before it ever reaches the player.

youtube: https://www.youtube.com/watch?v=ks5W6jwEURY

## Motivation — From Envy to Action

I grew up playing Minecraft and always admired modders who could turn their ideas into real in-game items. I wanted to do the same, but every time I opened a tutorial I hit a wall: Java, Gradle, Fabric API, resource pack formats — the learning curve was overwhelming, and I never knew where to start.

Then, at an MBZUAI admissions presentation, I heard about a senior's startup called ModCraft that could generate publishable mods from natural language. I was fascinated: how was this possible? Back home, I thought — I don't know much Java, but in the AI era anything seems possible. Could I build something similar myself?

So I started ModSmith. The goal was not to replace mod developers, but to let anyone with an idea — even without Java knowledge — turn that idea into a playable mod.

## Learning Path — Hand-Coding First, AI Second
<img width="1600" height="1004" alt="image" src="https://github.com/user-attachments/assets/df3c3991-9670-4b1e-b403-9ab2b5356c44" />

I read an article on the Fabric Wiki titled "Using LLMs for Minecraft Modding". It warned that beginners should not let LLMs write mods from scratch — you would miss the practice and have no ability to judge whether the AI-generated code is correct.

So I took the long route first. I taught myself IntelliJ IDEA and Java, then worked through the official Fabric tutorial manually. By typing every line myself, I understood the registry system, the relationship between Item and Item.Properties, the structure of resource packs and model JSONs, Gradle build flows, and the API differences between Minecraft versions.

Only after I had that foundation did I bring in AI. With the ability to judge correctness, I could now use LLMs as a multiplier instead of a crutch.

## Architecture & Implementation

The system architecture is built around a clear separation of concerns: LLMs handle the "what" (translating intent into a structured blueprint), while hand-written templates handle the "how" (generating compilable Java and resources). This keeps generation deterministic and debuggable.

### 📝 Blueprint Generation

LLM translates natural language into a verifiable JSON blueprint — structured, typed, and easy to validate before any code is produced.

### 🔧 Template-Based Codegen

Deterministic templates convert blueprints into Java source files, model JSONs, texture stubs, and Gradle build scripts — no "creative" code generation.

### ✅ Compile Verification

Auto-runs `./gradlew build`. Failures are fed back to the LLM to correct the blueprint, with up to 3 retry cycles.

### 🎮 Runtime Verification

Launches Minecraft, parses game logs, and checks that the mod loads and items register correctly — proof that it actually works.

## Two Modes — Chat & Execute

The web interface offers two distinct modes for two different workflows:

- **Chat Mode** — for iterative requirements clarification, powered by a Requirements Advisor agent that asks follow-up questions until the intent is fully specified.
<img width="2814" height="1520" alt="image" src="https://github.com/user-attachments/assets/4bfd7055-296c-4808-b64d-e43b31044bfa" />

- **Execute Mode** — for one-shot generation with live progress logging, so you can watch each stage (blueprint, codegen, build, verification) as it happens.
<img width="2814" height="1324" alt="image" src="https://github.com/user-attachments/assets/b2372e30-1b0e-41dc-b543-0c9162efb83e" />

Users can generate basic items, food items, and tools — each with their own template pipeline. The same blueprint drives both modes, so a spec refined in Chat Mode can be handed straight to Execute Mode without rewriting anything.

## Generated Content & In-Game Proof
<img width="2814" height="1452" alt="image" src="https://github.com/user-attachments/assets/3684ecc3-fba3-4457-988e-ef65bc4942c4" />

Every successful generation produces four downloadable artifacts:

- The full project source (ZIP)
- The installable mod JAR
- The blueprint JSON for reproducibility
- A README with installation instructions

The generated content panel shows the complete blueprint with all item properties, visual settings, and localization strings.

<img width="1100" height="649" alt="image" src="https://github.com/user-attachments/assets/48d74bd6-62f7-4d53-ab53-edb966175a9f" />
The ultimate test: launching Minecraft and seeing the generated item appear in the inventory. The in-game verification panel shows live log output from the game launch, confirming that the mod loads without errors and the custom items are registered.

In the screenshot above, the "Blue-Glowing Fruit" (generated from the description "Small, round, blue-glowing fruit") is visible both in the inventory slot and as a dropped item in the world.

## Reflection

Building it also taught me that "I don't know Java" is no longer a hard blocker. With the right architecture — templates for structure, AI for translation, verification for safety — you can build tools that let anyone create in domains that previously required years of training.
<img width="1017" height="572" alt="image" src="https://github.com/user-attachments/assets/76c69c46-9eb6-44a8-a06e-c493e7476838" />
