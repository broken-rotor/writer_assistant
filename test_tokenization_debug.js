// Test script to simulate the tokenization issue
// This will help us understand the flow without needing browser interaction

const fetch = require('node-fetch');

async function testTokenization() {
    console.log('🧪 Starting tokenization test...');
    
    const testText = "This is a test message for token counting functionality.";
    
    try {
        console.log('🚀 Making request to token counting API...');
        
        const response = await fetch('http://localhost:8000/api/v1/tokens/count', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:4200'
            },
            body: JSON.stringify({
                texts: [
                    {
                        text: testText,
                        content_type: 'system_prompt'
                    }
                ],
                strategy: 'exact',
                include_metadata: true
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Received response:', JSON.stringify(data, null, 2));
        
        // Simulate the frontend processing
        console.log('📊 Simulating frontend processing...');
        console.log('Token count:', data.results[0].token_count);
        console.log('Success:', data.success);
        
        return data;
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        throw error;
    }
}

// Run the test
testTokenization()
    .then(() => {
        console.log('🎉 Test completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        console.error('💥 Test failed:', error);
        process.exit(1);
    });

