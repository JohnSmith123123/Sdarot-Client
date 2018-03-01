import sdarot
import requests
import multiprocessing 
import time
import functools


REQUEST_CHUNK_SIZE = 1024 * 1024 # 1 MB


class SdarotEpisodeDownloader(object):
    def __init__(self, episode, jobs=5):
        self._jobs = jobs
        self._link_gen = episode.generate_url

    def _create_links(self, count):
        pool = multiprocessing.Pool(processes=count)
        urls = []
        for _ in range(count):
            url = pool.apply_async(self._link_gen)
            urls.append(url)
            # I guess the server's random is based on time
            # We must wait to get a different server
            time.sleep(2)
        pool.close()
        pool.join()
        return [url.get() for url in urls]

    def start(self, output_path):
        urls = self._create_links(self._jobs)
        r = requests.head(urls[0])
        headers = r.headers
        assert headers['Accept-Ranges'] == 'bytes'
        self._total_size = int(headers['Content-Length'])
        self._chunk_size = int(self._total_size / len(urls)) + 1

        chunks = ((s, s + self._chunk_size - 1) for s in range(0, self._total_size, self._chunk_size))

        manager = multiprocessing.Manager()
        write_queue = manager.Queue()
        pool = manager.Pool(processes=(len(urls) + 1))
        writer = pool.apply_async(self._file_writer, (output_path, write_queue))
        params = [(urls.pop(), a, b, write_queue) for a, b in chunks]
        chunks_data = pool.map(self._download_chunk, params)
        pool.close()
        write_queue.put(None) # Close the file
        writer.wait()
        pool.terminate()

    @staticmethod
    def _file_writer(path, queue):
        chunk_number = 0
        with open(path, "wb") as f:
            while True:
                msg = queue.get()
                if msg is None:
                    print("Done writing to file.")
                    break
                loc, data = msg
                chunk_number += 1
                print("Writing {} bytes to location {} (Chunk #{})".format(len(data), loc, chunk_number))
                f.seek(loc)
                f.write(data)
                f.flush()

    @staticmethod
    def _download_chunk(args):
        url, start, end, queue = args
        print("Downloading a {} bytes chunk from {}".format(end - start + 1, url))
        r = requests.get(url, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Range': 'bytes={}-{}'.format(start, end),
        })
        offset = start
        for chunk in r.iter_content(chunk_size=REQUEST_CHUNK_SIZE):
            queue.put((offset, chunk))
            offset += len(chunk)


def lg():
    return 'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_30mb.mp4'


def main():
    s = SdarotEpisodeDownloader(lg)
    s.start("output.mp4")


if __name__ == '__main__':
    main()
