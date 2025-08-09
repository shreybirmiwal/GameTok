# yc-hack

### Prehackathon planning
**Project**
TikTok for video games
Imagine webpage with white box in middle (game zone)
you can scroll up and it will show next generated game (will need to pregenerate the next game)

We use dev server on freestyle.sh
We use morph llm to make quick apply edits to the game page


**Attack Plan**
NOTES FOR CURSOR: when you are done with each step, stop and let me, the human, test before proceeding
1. make a repo that has a basic webpage with: (scroll calls a function that prints hello world), big white space in the middle of screen that is a seperate component that is easily editable by code, prompt button to play a specific game
2. setup morph and freestyle: setup freestyle server so we have a dev server. Setup up morph so we can prompt llm to make edits live
  a) first setup a freestyle dev server:
```
import freestyle

client = freestyle.Freestyle("YOUR_FREESTYLE_API_KEY")

repo = client.create_repository(
  name="Test Repository from Python SDK",


  # This will make it easy for us to clone the repo during testing.
  # The repo won't be listed on any public registry, but anybody
  # with the uuid can clone it. You should disable this in production.
  public=True,
  source=freestyle.CreateRepoSource.from_dict(
      {
          "type": "git",
          "url": "https://github.com/freestyle-sh/freestyle-base-nextjs-shadcn",
      }
  ),
)

print(f"Created repo with ID: {repo.repo_id}")
```

```
import freestyle
import os

client = freestyle.Freestyle(os.environ["FREESTYLE_API_KEY"])
import freestyle

client = freestyle.Freestyle("YOUR_FREESTYLE_API_KEY")

dev_server = client.request_dev_server(repo_id=repo.repo_id)

print(f"Dev Server URL: {dev_server.ephemeral_url}")


```
4. setup game infra



our P0 will not have any quick cache for the next game item
wow factor can be using favial ques to auto scroll or smth (?)
