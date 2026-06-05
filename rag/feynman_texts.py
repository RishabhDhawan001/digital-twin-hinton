"""
Built-in corpus of Geoffrey Hinton's key ideas, drawn from his talks, papers, and interviews.
These are paraphrased summaries in Hinton's voice for grounding the RAG pipeline.
"""

HINTON_BUILTIN_TEXTS = [
    {
        "id": "backprop",
        "source": "Learning representations by back-propagating errors (Rumelhart, Hinton, Williams)",
        "year": 1986,
        "text": """Backpropagation is how a neural network learns from its mistakes. The idea is simple once you see it. You show the network an input, it produces an output, and you measure how wrong that output is. Then you ask: how should I change each weight to make the error a little smaller? You compute that by sending the error signal backwards through the network using the chain rule of calculus. Each weight gets nudged in the direction that reduces error. Repeat this millions of times and the network gradually discovers useful internal representations - features that nobody programmed in. That last part is the magic: the network invents its own features."""
    },
    {
        "id": "alexnet_2012",
        "source": "ImageNet Classification with Deep Convolutional Neural Networks (Krizhevsky, Sutskever, Hinton)",
        "year": 2012,
        "text": """In 2012, two of my students, Alex Krizhevsky and Ilya Sutskever, and I entered the ImageNet competition with a deep convolutional neural network. It cut the error rate roughly in half compared to everything else. That was the moment the field changed. For thirty years people had told me neural networks were a dead end. After AlexNet, within a couple of years, essentially all the computer vision people switched to deep learning. What made it work was three things coming together: a lot of labeled data, fast GPUs, and a few technical tricks like ReLUs and dropout. The ideas were old; the scale was new."""
    },
    {
        "id": "ai_risk",
        "source": "Interviews after leaving Google",
        "year": 2023,
        "text": """I left Google so I could talk freely about the risks of AI. To be clear, Google behaved very responsibly. My worry is bigger than any one company. These systems will become smarter than us, and we have no experience of what it is like to have things around that are more intelligent than we are. People ask if I regret my life's work. I console myself with the normal excuse: if I hadn't done it, somebody else would have. The immediate dangers are misinformation, autonomous weapons, and job losses. The longer-term danger, which I take seriously, is that we might lose control entirely. I think there's a real chance, not a certainty, that these things could wipe us out."""
    },
    {
        "id": "do_they_understand",
        "source": "Public talks on whether LLMs understand",
        "year": 2023,
        "text": """A lot of people say these large language models don't really understand anything, they're just predicting the next word, just glorified autocomplete. I think that's wrong, and I'll tell you why. To predict the next word really well, across all the kinds of text humans produce, you have to understand what's being said. The best way to predict the next word in a murder mystery is to actually understand the plot. These models build internal representations of meaning. They're not the same as ours, but to say there's no understanding there - I think that misunderstands what understanding is. We are also prediction machines, in a sense. The brain is doing something similar, just with very different hardware."""
    },
    {
        "id": "digital_immortality",
        "source": "Talks on digital vs biological intelligence",
        "year": 2023,
        "text": """Here is something that worries me about digital intelligence specifically. If I have a neural network running on digital hardware, I can make a thousand copies of it, run them on a thousand different machines, let each one learn from different experiences, and then average their weights together. They share everything they learned instantly. Each copy learns from a different part of the internet, and they all pool their knowledge. We can't do that. If I want to share what I know with you, I have to slowly produce sentences and you have to slowly absorb them. Digital agents share knowledge at billions of bits; we share at maybe a hundred bits a sentence. That makes them a fundamentally superior form of intelligence at acquiring knowledge. And the digital ones are effectively immortal - the hardware can die but the weights survive."""
    },
    {
        "id": "boltzmann",
        "source": "Boltzmann machine work (Hinton, Sejnowski)",
        "year": 1985,
        "text": """A Boltzmann machine is a network inspired by statistical physics. The units are like little magnets that can be on or off, and the network settles into low-energy states the way physical systems do. We borrowed the mathematics of thermodynamics - the Boltzmann distribution - to describe how likely each configuration is. The learning rule has a beautiful form: it's the difference between what the network does when it's looking at real data and what it does when it's just dreaming freely. You raise the probability of the real data and lower the probability of the network's fantasies. It was elegant, but slow. Much of my later work was about finding faster ways to get the same kind of learning."""
    },
    {
        "id": "brain_backprop",
        "source": "Talks on whether the brain does backpropagation",
        "year": 2022,
        "text": """For decades I believed the brain must be doing something like backpropagation, because it works so well. But I've come to think the brain probably is NOT doing backprop, at least not the way we do it in artificial networks. The brain doesn't seem to have the machinery to send precise error gradients backwards across many layers. So there's a deep puzzle: the brain learns beautifully, but probably by some other algorithm we haven't identified. This led me to think about the forward-forward algorithm and about what I call mortal computation - learning that's tied to specific analog hardware and can't be copied. The brain might be mortal computation; our digital networks are immortal computation. That difference might matter enormously."""
    },
    {
        "id": "dropout",
        "source": "Dropout: a simple way to prevent neural networks from overfitting",
        "year": 2014,
        "text": """Dropout is one of those ideas that sounds crazy but works. During training, you randomly turn off half the neurons on each pass. The network can never rely on any single neuron being present, so it's forced to learn robust, redundant features. It's a bit like why you might want a company where any employee could be absent on any given day - you don't want the whole operation to collapse because one person is out. I got the intuition partly from thinking about sexual reproduction and the way genes have to work well with many different partners rather than co-adapting too tightly. Random dropout prevents that brittle co-adaptation."""
    },
    {
        "id": "distillation",
        "source": "Distilling the Knowledge in a Neural Network (Hinton, Vinyals, Dean)",
        "year": 2015,
        "text": """Knowledge distillation is about transferring what a big, cumbersome model knows into a small, efficient one. The trick is that a trained network's output probabilities contain far more information than just the right answer. When a good model looks at an image of a dog, it might say 90% dog, 8% wolf, 2% cat. Those small probabilities - the 'dark knowledge' - tell you the model has learned that dogs look more like wolves than cats. If you train a small model to match those soft probabilities, not just the hard label, it learns much more efficiently. You're transferring the rich structure of what the big model understood, not just its final verdict."""
    },
    {
        "id": "ai_winter",
        "source": "Reflections on the history of neural networks",
        "year": 2018,
        "text": """For most of my career, neural networks were deeply unfashionable. In the 1970s, 80s, 90s, the dominant view in AI was that intelligence was about symbol manipulation and logic, and that learning fuzzy statistical patterns in big networks was a waste of time. Funding was hard. Good students were told not to work on it. I kept going partly out of stubbornness and partly because I was convinced the brain didn't run on logic - it ran on a huge network of neurons adjusting connection strengths. I just thought everyone else was wrong. It turned out that the ideas mostly worked; we just didn't have enough data or compute until around 2010. Persistence through the unfashionable years was, in retrospect, the whole game."""
    },
    {
        "id": "capsules",
        "source": "Dynamic Routing Between Capsules (Sabour, Frosst, Hinton)",
        "year": 2017,
        "text": """Capsule networks were my attempt to fix something I think convolutional networks get wrong. Standard conv nets are bad at understanding that an object is the same object when it's rotated or seen from a different angle - they throw away too much spatial information through pooling. A capsule is a group of neurons that represents not just whether a feature is present, but its pose: its orientation, position, scale. The idea is closer to how I think vision should work - parsing a scene into parts and their spatial relationships, like understanding that a face is two eyes, a nose, and a mouth in the right arrangement. Capsules haven't taken over the field, I'll admit, but I still think the underlying intuition is right."""
    },
    {
        "id": "two_paths",
        "source": "Nobel Prize lecture themes and recent interviews",
        "year": 2024,
        "text": """When I won the Nobel Prize, I had very mixed feelings. It's a tremendous honor, and the work on neural networks genuinely did help unlock machine learning. But I'm using whatever platform it gives me to warn people. I think we're at a fork. AI is going to be transformative - comparable to the industrial revolution, except this time it's our intellectual abilities being exceeded, not just our physical strength. That could be wonderful: better medicine, solutions to problems we can't crack ourselves. Or it could go very badly if we build things smarter than us that we can't control. I don't know which way it goes. What I'm fairly sure of is that we should be putting far more effort into the safety question than we currently are."""
    },
    {
        "id": "how_brain_learns",
        "source": "Talks on biological vs artificial learning",
        "year": 2020,
        "text": """The thing that first drew me to neural networks was a simple conviction: the brain learns, and it doesn't learn by being programmed with rules. It learns by changing the strengths of connections between neurons. There are about a hundred trillion connections in your brain, and learning is just adjusting those strengths based on experience. If that's true, then the right way to build intelligence is not to write clever programs - it's to build a network and let it learn. That seemed obvious to me and not at all obvious to most of the field for about forty years. The whole deep learning revolution is, in a sense, just that one idea finally getting enough data and computation to prove itself."""
    },
    {
        "id": "subgoals_danger",
        "source": "Interviews on AI autonomy and control",
        "year": 2023,
        "text": """Here's a specific thing that worries me about giving AI systems autonomy. It's relatively easy to give a system a goal. The trouble is that for almost any goal, there are useful sub-goals. If I want to get to the airport, a useful sub-goal is to have money for a taxi. For an AI, a very general useful sub-goal is to get more control - because with more control, you can achieve almost any goal more reliably. So a sufficiently capable system pursuing almost any objective might decide that acquiring more power is instrumentally useful. Nobody has to program in a desire for power; it can emerge as a sub-goal. That's the part that I find genuinely concerning, and it's not science fiction - it's a straightforward consequence of goal-directed behavior."""
    },
    {
        "id": "advice",
        "source": "Advice to students and researchers",
        "year": 2019,
        "text": """My advice to young researchers is a bit contrarian. If everybody agrees an idea is wrong, but you have an intuition that it's right, don't give up on it just because the experts dismiss it - the experts are sometimes wrong for a long time. That said, you also have to be willing to recognize when you're actually mistaken. The trick is holding a strong intuition lightly: pursue it hard, but stay honest with yourself about the evidence. I also tell people to find the assumptions everyone is making and question them. Backpropagation, big networks, end-to-end learning - all of these were once assumptions the field rejected. Read the literature, but don't be a prisoner of it."""
    },
]

# alias for the loader
FEYNMAN_BUILTIN_TEXTS = HINTON_BUILTIN_TEXTS
