from dash import Input, Output, clientside_callback, State

# Initialize Plaid Link
clientside_callback(
    """
    async function(n_clicks) {
        if (!n_clicks) return;
        
        try {
            const response = await fetch("/api/create_link_token", {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.error) {
                console.error("Error fetching link token:", data.error);
                return;
            }
            
            const handler = Plaid.create({
                token: data.link_token,
                onSuccess: async (public_token, metadata) => {
                    try {
                        const exchangeResponse = await fetch("/api/exchange_public_token", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            credentials: 'include',
                            body: JSON.stringify({ public_token }),
                        });
                        const exchangeData = await exchangeResponse.json();
                        
                        if (exchangeData.access_token) {
                            // Update the store with the access token
                            window.dash_clientside.no_update = false;
                            return exchangeData.access_token;
                        }
                    } catch (error) {
                        console.error('Token exchange failed:', error);
                    }
                },
                onExit: (err, metadata) => {
                    if (err) console.error('Link exit error:', err);
                }
            });
            
            handler.open();
        } catch (error) {
            console.error('Plaid initialization failed:', error);
        }
    }
    """,
    Output('access-token-store', 'data'),
    Input('link-button', 'n_clicks'),
    prevent_initial_call=True
)