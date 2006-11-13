#!/bin/bash
#
# Download dependencies that would be necessary to build the
# pl_netflow and pl_conf root slices from the vserver-reference image.
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2004-2006 The Trustees of Princeton University
#
# $Id: system-packages.sh,v 1.3 2006/07/01 18:13:31 mlhuang Exp $
#

export PATH=/sbin:/bin:/usr/sbin:/usr/bin

vroot=$PWD/vservers/.vref/default
rpms=$PWD/vservers/system-packages
install -d -m 755 $rpms

# curl can't list file:// URLs
list ()
{
    url=$1
    if [ -e ${url#file://} ] ; then
	/bin/ls ${url#file://}
    else
	curl --fail --silent --max-time 60 $url
    fi
}

# Space separated list of required packages
planetflow="netflow"

for vref in planetflow ; do
    packages=${!vref}
    dependencies=()

    if yum --help | grep -q shell ; then
	while read -a words ; do
	    if [ ${#words[*]} -lt 5 ] ; then
		continue
	    fi

	    # netflow i386 3.1-23.planetlab.2006.04.04 bootstrap 61 k
	    package=${words[0]}
	    arch=${words[1]}
	    version=${words[2]}
	    # Remove the epoch from the version
	    version=${version##*:}
	    repository=${words[3]}

	    baseurl=
	    while read line ; do
		if [ -z "$line" ] ; then
		    continue
		elif grep -q "^\[$repository\]" <<<$line ; then
		    baseurl=$repository
		elif [ "$baseurl" = "$repository" ] && grep -q "^baseurl=" <<<$line ; then
		    eval $line

		    # We could parse headers/header.info and/or
		    # repodata/primary.xml.gz to figure out where the
		    # package actually is within the repository, but
		    # it would be too much trouble. Just try
		    # downloading it from one of the common
		    # subdirectories.
		    echo "* $vref: $repository $package-$version.$arch.rpm"
		    for subdirectory in "" Fedora/RPMS $arch ; do
			if curl --fail --silent --max-time 60 $baseurl/$subdirectory/$package-$version.$arch.rpm \
			    >$rpms/$package-$version.$arch.rpm ; then
			    break
			fi
			rm -f $rpms/$package-$version.$arch.rpm
		    done

		    # Assert that we got it successfully
		    if [ ! -f $rpms/$package-$version.$arch.rpm ] ; then
			echo "Failed to fetch $package-$version.$arch.rpm from $repository" >&2
			false
		    fi

		    dependencies[${#dependencies[*]}]=$package-$version.$arch.rpm
		    break
		fi
	    done <$vroot/etc/yum.conf
	done < <((yum -c $vroot/etc/yum.conf --installroot=$vroot shell <<EOF
install $packages
transaction solve
transaction list
EOF
	    ) | sed -ne '/^Installing:/,/^Transaction Summary/p' 
	)
    else
        # This is pretty fucked up. Turn on verbose debugging and the
        # --download-only option, which, contrary to what you might
        # think the option means, downloads the headers, not the
        # packages themselves. In any case, verbose debugging prints
        # out the baseURL and path of each RPM that it would download
        # if --download-only were not specified.
	baseURL=
	path=
	while read line ; do
	    if [ -z "$baseURL" ] ; then
		baseURL=$(sed -ne 's/failover: baseURL = \(.*\)/\1/p' <<<$line)
	    elif [ -z "$path" ] ; then
		path=$(sed -ne 's/failover: path = \(.*\)/\1/p' <<<$line)
	    else
		if [ "${path##*.}" = "rpm" ] ; then
		    echo "* $vref: $(basename $path)"
		    curl --fail --silent --max-time 60 $baseURL/$path >$rpms/$(basename $path)
		    dependencies[${#dependencies[*]}]=$(basename $path)
		fi
		baseURL=
		path=
	    fi
	done < <(yum -d 3 -c $vroot/etc/yum.conf --installroot=$vroot -y --download-only install $packages 2>&1)
    fi

    for dependency in "${dependencies[@]}" ; do
	echo $dependency
    done >$rpms/$vref.lst
done

# Clean yum cache
yum -c $vroot/etc/yum.conf --installroot=$vroot -y \
    clean all

# Clean RPM state
rm -f $vroot/var/lib/rpm/__db*

exit 0
