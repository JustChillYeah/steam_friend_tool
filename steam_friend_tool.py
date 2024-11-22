import requests
import re

# Global cache for storing friends lists
friends_cache = {}

# Step 1: Get the friends list of the main Steam ID
def get_friends(steamid, api_key):
    # Check if the friends list for this Steam ID is already cached
    if steamid in friends_cache:
        print(f"Using cached data for SteamID {steamid}")
        return friends_cache[steamid]
    
    # If not cached, make the API request
    url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={api_key}&steamid={steamid}&relationship=friend'
    response = requests.get(url)
    
    if response.status_code == 200:
        friends_data = response.json()
        # Cache the friends list
        friends_cache[steamid] = friends_data
        return friends_data
    else:
        # If the API doesn't return friends, assume it's a private profile
        print(f"Could not retrieve friends list for SteamID {steamid}. The profile may be private.")
        return {}

# Step 2: Get player summaries for a list of Steam IDs
def get_player_summaries(steamids, api_key):
    ids = ','.join(str(id) for id in steamids)
    url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={ids}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Could not retrieve player summaries for SteamIDs {steamids}")
        return {}

# Step 3: Search for a nickname within a list of Steam IDs
def search_for_nickname_in_friendlist(friends, nickname, api_key):
    found_profiles = []  # List to store profiles where the nickname is found
    
    # Split the nickname into individual words
    nickname_words = nickname.lower().split()

    for friend in friends:
        steamid = friend['steamid']
        # Fetch the player's summary to get the nickname
        player_data = get_player_summaries([steamid], api_key)
        
        # Check if player data is valid and exists
        if 'response' not in player_data or 'players' not in player_data['response'] or len(player_data['response']['players']) == 0:
            print(f"Could not retrieve data for SteamID {steamid}. The profile may be private or invalid.")
            continue
        
        player_name = player_data['response']['players'][0]['personaname']

        print(f"Checking friend {player_name} (SteamID: {steamid})...")

        # Get that friend's friends list (cached)
        friend_friends_data = get_friends(steamid, api_key)
        
        if 'friendslist' not in friend_friends_data:
            print(f"Could not retrieve friends list for {player_name}. The profile may be private.")
            continue
        
        # Search through the friend's friends list for the nickname
        friend_friends = friend_friends_data['friendslist']['friends']
        for friend_of_friend in friend_friends:
            friend_of_friend_steamid = friend_of_friend['steamid']
            friend_of_friend_data = get_player_summaries([friend_of_friend_steamid], api_key)
            
            # Check if friend's data is valid and exists
            if 'response' not in friend_of_friend_data or 'players' not in friend_of_friend_data['response'] or len(friend_of_friend_data['response']['players']) == 0:
                print(f"Could not retrieve data for friend of friend {friend_of_friend_steamid}. The profile may be private or invalid.")
                continue
            
            friend_of_friend_name = friend_of_friend_data['response']['players'][0]['personaname']
            
            # Check if the friend's name matches the full nickname (case-insensitive and exact match)
            pattern = r'\b' + r'\b|\b'.join(re.escape(word) for word in nickname_words) + r'\b'
            if re.search(pattern, friend_of_friend_name.lower()):
                found_profiles.append({
                    'friend_of_friend_name': friend_of_friend_name,
                    'friend_of_friend_steamid': friend_of_friend_steamid,
                    'player_name': player_name,
                    'player_steamid': steamid
                })
    
    # After all checks, display found profiles
    if found_profiles:
        print(f"\nNickname '{nickname}' found in the following profiles:")
        for profile in found_profiles:
            print(f"Found on {profile['friend_of_friend_name']} (SteamID: {profile['friend_of_friend_steamid']}) in {profile['player_name']}'s friends list (SteamID: {profile['player_steamid']})")
    else:
        print(f"\nNo profiles found with the nickname '{nickname}' in the searched friends lists.")

# Step 4: Read the API key from a file
def read_api_key():
    try:
        with open("api_key.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

# Step 5: Prompt user for API key and create the text file if not found
def prompt_and_save_api_key():
    api_key = input("API key file not found. Please enter your Steam API key: ")
    try:
        with open("api_key.txt", "w") as file:
            file.write(api_key)
        print("API key saved successfully to 'api_key.txt'.")
        return api_key
    except Exception as e:
        print(f"Failed to save API key: {e}")
        return None

# Main function to execute the search
def main():
    # Step 1: Read API Key from the text file
    api_key = read_api_key()
    
    if api_key is None:
        api_key = prompt_and_save_api_key()
        if api_key is None:
            return
    
    while True:  # Loop to allow multiple searches without restarting the program
        # Step 2: Ask for user input
        steamid = input("Enter the SteamID of the user you want to search: ")
        nickname = input("Enter the nickname you want to search for: ")
        
        # Step 3: Get the friends list of the target user
        friends_list_data = get_friends(steamid, api_key)
        
        if 'friendslist' not in friends_list_data:
            print("Error: Could not retrieve friends list. The profile may be private.")
            return
        
        # Step 4: Get the Steam IDs of the friends
        friends = friends_list_data['friendslist']['friends']

        # Step 5: Search each friend's list for the nickname
        print(f"Searching friends of SteamID {steamid} for nickname '{nickname}'...")
        search_for_nickname_in_friendlist(friends, nickname, api_key)

        # Ask the user if they want to search again or quit
        user_choice = input("\nPress 'Y' to search again or 'Q' to quit: ").lower()
        if user_choice == 'q':
            print("Exiting the program. Goodbye!")
            break
        elif user_choice != 'y':
            print("Invalid input, exiting program.")
            break

# Run the tool
if __name__ == '__main__':
    main()
