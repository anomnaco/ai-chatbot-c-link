document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submitBtn');
    const userQuery = document.getElementById('userQuery');
    const resultsContainer = document.getElementById('results');
    const errorMessage = document.getElementById('error');

    submitBtn.addEventListener('click', async () => {
        const query = userQuery.value.trim();
        if (!query) {
            errorMessage.textContent = 'Query cannot be empty.';
            return;
        }

        resultsContainer.innerHTML = '<p>Loading...</p>';
        errorMessage.textContent = '';

        try {
            console.log('Sending request to server...');
            const response = await fetch('http://localhost:5000/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
                mode: 'cors'
            });

            console.log('Response received:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received data:', data);

            if (data.error) {
                throw new Error(data.error);
            }

            // Extract the JSON string from the response
            const jsonMatch = data.results.text.data.text.match(/\`\`\`json\n([\s\S]*?)\n\`\`\`/);
            if (!jsonMatch) {
                throw new Error('No JSON data found in the response');
            }

            const parsedData = JSON.parse(jsonMatch[1]);
            console.log('Parsed data:', parsedData);

            displayResults(parsedData);
        } catch (err) {
            console.error('Error:', err);
            errorMessage.textContent = `Error: ${err.message}. Please check your network connection and try again.`;
            resultsContainer.innerHTML = ''; // Clear loading message
        }
    });

    function displayResults(data) {
        resultsContainer.innerHTML = ''; // Clear previous results
        const jsonMatch = data.results.text.data.text.match(/\`\`\`json\n([\s\S]*?)\n\`\`\`/);
        if (!jsonMatch) {
            console.error('No JSON data found in the text');
            return;
        }

        const parsedData = JSON.parse(jsonMatch[1]);
        console.log('Parsed data displayResults:', parsedData);

        const hasProducts = parsedData.products && parsedData.products.length > 0;
        const hasRecipes = parsedData.recipes && parsedData.recipes.length > 0;

        // Determine the layout based on available data
        if (hasProducts && !hasRecipes) {
            createFullWidthSection('Products', parsedData.products, createProductCard);
        } else if (!hasProducts && hasRecipes) {
            createFullWidthSection('Recipes', parsedData.recipes, createRecipeCard);
        } else if (hasProducts && hasRecipes) {
            const productsSection = createSection('Products');
            parsedData.products.forEach(product => {
                productsSection.appendChild(createProductCard(product));
            });
            resultsContainer.appendChild(productsSection);

            const recipesSection = createSection('Recipes');
            parsedData.recipes.forEach(recipe => {
                recipesSection.appendChild(createRecipeCard(recipe));
            });
            resultsContainer.appendChild(recipesSection);
        } else {
            resultsContainer.innerHTML = '<p>No results found.</p>';
        }

        console.log("Results Container:", resultsContainer.innerHTML);

        // Initialize image carousels after adding cards to the DOM
        initializeImageCarousels();
    }

    function createFullWidthSection(title, items, cardCreator) {
        const section = createSection(title);
        section.classList.add('full-width');
        items.forEach(item => {
            section.appendChild(cardCreator(item));
        });
        resultsContainer.appendChild(section);
    }

    function createProductCard(product) {
        return createCard(
            product.title,
            `<p>${product.description}</p>
             <p class="price">$${product.price}</p>`,
            product.url,
            'View Product',
            product.images
        );
    }

    function createRecipeCard(recipe) {
        return createCard(
            recipe.title,
            `<p>${recipe.description}</p>`,
            recipe.url,
            'View Recipe',
            [recipe.image_url]
        );
    }

    function createSection(title) {
        const section = document.createElement('div');
        section.className = 'section';
        const header = document.createElement('h2');
        header.textContent = title;
        section.appendChild(header);
        return section;
    }

    function createCard(title, content, url, linkText, images) {
        const card = document.createElement('div');
        card.className = 'card';

        let imageCarousel = '';
        if (images && images.length > 0) {
            imageCarousel = `
                <div class="image-carousel">
                    ${images.map((img, index) => `
                        <img src="${img}" alt="${title} - Image ${index + 1}" class="card-image ${index === 0 ? 'active' : ''}" data-index="${index}">
                    `).join('')}
                    ${images.length > 1 ? `
                        <button class="carousel-btn prev">&lt;</button>
                        <button class="carousel-btn next">&gt;</button>
                    ` : ''}
                </div>
            `;
        }

        card.innerHTML = `
            ${imageCarousel}
            <h3>${title}</h3>
            ${content}
            <a href="${url}" target="_blank" rel="noopener noreferrer">${linkText}</a>
        `;
        return card;
    }

    function initializeImageCarousels() {
        document.querySelectorAll('.image-carousel').forEach(carousel => {
            const images = carousel.querySelectorAll('.card-image');
            const prevBtn = carousel.querySelector('.carousel-btn.prev');
            const nextBtn = carousel.querySelector('.carousel-btn.next');

            if (images.length <= 1) return; // No need for carousel controls if there's only one image

            let currentIndex = 0;

            const showImage = (index) => {
                images.forEach(img => img.classList.remove('active'));
                images[index].classList.add('active');
            };

            prevBtn.addEventListener('click', () => {
                currentIndex = (currentIndex - 1 + images.length) % images.length;
                showImage(currentIndex);
            });

            nextBtn.addEventListener('click', () => {
                currentIndex = (currentIndex + 1) % images.length;
                showImage(currentIndex);
            });
        });
    }
});

