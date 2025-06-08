FROM ubuntu:22.04

# Install SSH server, Python, and necessary tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip && \
    mkdir /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    echo "root:secret" | chpasswd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the emulator script as `sensors` in PATH
COPY sensors_emulator.py /usr/local/bin/sensors
RUN chmod +x /usr/local/bin/sensors

EXPOSE 22

# Start SSH daemon in foreground
CMD ["/usr/sbin/sshd", "-D"]