# Introduction

In this application, I designed and implemented a file system that uses cloud object storage. At its core, this application is composed of two key components. First, I introduce the concept of the "object store." By default, I utilize Google Cloud Storage which is the S3 equivalent, providing a robust and reliable foundation for our cloud-based file system. 
The second component is the FUSE (Filesystem in User Space) file system interface. Traditionally, file systems are implemented within the operating system kernel. FUSE essentially acts as the intermediary that allows the kernel to "forward" file system calls to the user-space FUSE handler, providing a bridge between the user and the cloud object storage.
The primary challenge lies in the effective implementation and handling of the diverse file system calls that enable seamless interaction with cloud-based data. While the default API for libfuse is in C, I explore it by utilizing bindings in Python called fusepy.

# Design Details
In the context of a FUSE (Filesystem in Userspace) implementation for cloud object storage, following are fundamental file and directory operations that has been implemented:

## File Operations:

1.	Mount: Mounting refers to the process of associating FUSE file system with a directory in the local file system. When you mount your FUSE file system, it becomes accessible at a specified mount point, enabling users to interact with cloud-based storage as if it were a traditional local file system.
2.	Create: The "create" operation is used to create a new file within the file system. This operation allows users to generate new files in the cloud object storage, specifying the file name 
3.	Open: The "open" operation is used to access an existing file in the cloud object storage. When a file is opened, it can be read, written to, or otherwise manipulated. This operation ensures that a file is ready for read or write operations.
4.	Read: The "read" operation enables users to retrieve data from a file. It is used to read the content of a file and return it to the user or application.
5.	Write: The "write" operation allows users to modify the content of a file by writing data to it. This operation is essential for updating or creating new content within a file.
6.	Close: The "close" operation is used to end the access to a file that was previously opened. In my program, “release” method implements this. 

## Directory Operations:

1.	Mkdir: The "mkdir" operation is used to create a new directory within the file system. 
2.	Opendir: the "opendir" operation is essential for opening and accessing a directory. This operation is particularly important for navigating directories and listing their contents. 
3.	Readdir: The "readdir" operation allows users to list the contents of a directory. When a directory is opened with "opendir," "readdir" retrieves the list of files and subdirectories within that directory. 
4.	Rmdir: The "rmdir" operation is used to remove (delete) a directory from the file system. 

## Optional Operations:

1.	Unlink (Delete): The "unlink" operation is used to delete a file from the cloud object storage. It permanently removes the file.
2.	Rename: The "rename" operation allows users to change the name of a file or move it to a different location within the file system.

# Implementation and GCP: Google Bucket Storage
To implement this, the FUSE agent runs on the local machine, in my case a VM instance with the following specifications:
gcloud compute instances create instanceubuntu \
  --zone=us-central1-a \
  --machine-type=g1-small \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --network=psnetwork
This was also done to solve the issue of root permission problems associated with macOS. 
For each operation, FUSE handler intercepts them and invokes appropriate cloud storage call using google cloud bucket APIs. In order to implement this, I leveraged the fusepy library, a Python binding of the libfuse library which intercepts file system operations and invokes the appropriate cloud storage calls using the Google Cloud Bucket APIs.

# Testing
I ran the following commands on the terminal to test the implemented code:
•	mkdir testfolder 
(This tests the mkdir method:  before calling this method, it calls the getattr method, followed by mkdir method)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/207f39d9-1dca-4fcc-a8f8-4a04e65358cc)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/431b1885-0e05-4f4a-9d3e-b2ba6677aa69)


 
•	touch testfile.txt
(This method tests the create function: flow of functions observed: getattr, create, utimens, getattr, release, opendir, readdir)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/9646163f-2425-4144-95e3-3404773aab1e)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/35f27865-b221-4e9c-8475-557dc892b049)


 
•	echo “hi I am inside testfile.txt”  >> testfile.txt
(this tests overall flow -> getattr, file create, write, release )

![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/e82fb4e4-5c8d-485b-96fb-c235e3c0c67c)

 
•	cat testfile.txt >> output.txt
(getattr, create /output.txt, open /testfile.txt, read testfile.txt, write output.txt, release testfile, release output.txt)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/b19d401d-816a-4a9b-bc6f-ad4459bdde21)
![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/af800ec3-d54a-48db-ad44-7ba4eb2b59c5)

 
•	ls
(getattr, opendir, readdir)

![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/9cc45732-c1b6-4215-a7cf-3a17d175740f)

 
•	mv output.txt testoutput.txt
(getattr, rename)

 ![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/14d34041-46e5-4b01-a4ef-8b0bf88c6b9e)

![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/bfbb08c1-02cd-4809-bd1a-79d2cfc58423)

•	rm testoutput.txt
(getattr, access, unlink)

![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/88e8033e-e44e-43eb-83aa-289609998d35)
![image](https://github.com/human-doodle/File-systems-using-cloud-storage/assets/46643099/40b0c879-e635-42e5-badb-97f6a3aafcb5)


 
 
# Limitations
Implementing a cloud-based FUSE file system might impose potential limitations. One of the concern is the increased latency associated with network communication between the local system and the cloud storage service, impacting the speed of read and write operations. Throughput may be constrained by the bandwidth between systems. Additionally, cloud providers may impose API rate limits, affecting the file system's ability to handle numerous operations. 

# References :
•	https://github.com/libfuse/libfuse/blob/master/example/passthrough.c#L210

•	https://github.com/fusepy/fusepy/blob/master/fuse.py#L647

•	https://www.cs.hmc.edu/~geoff/classes/hmc.cs135.201001/homework/fuse/fuse_doc.html#readdir-details

•	https://web.eecs.utk.edu/~jplank/plank/classes/cs360/360/notes/Stat/lecture.html#:~:text=opendir()%20opens%20the%20directory,free%27s%20the%20%22struct%20dirent%22.

•	https://gist.github.com/bkmeneguello/5884492

•	https://www.cs.nmsu.edu/~pfeiffer/fuse-tutorial/html/unclear.html

•	https://sar.informatik.hu-berlin.de/teaching/2013-w/2013w_osp2/lab/Lab-4-FUSE/lab-FUSE_.pdf

•	https://www.ibm.com/docs/en/zos/2.3.0?topic=functions-opendir-open-directory


# Files:
•	Passthrough.py : python file implementing file system that uses cloud storage.
