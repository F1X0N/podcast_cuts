def pipeline(episode_url):
    video = download(episode_url)
    transcript = transcribe(video)
    hl = find_highlights(transcript, n=3)
    for h in hl:
        clip = make_clip(video, h, transcript)
        thumb = gen_thumbnail(h["hook"])
        desc = f"{h['hook']} • Trecho do podcast XYZ\n\nAssista completo: {episode_url}"
        upload(clip, h["hook"], desc)        # YouTube
        # tiktok_upload(clip, h["hook"])     # se API liberada
